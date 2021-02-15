import datetime
import json
from typing import Iterable

import mailjet_rest.client
from requests import Response

from pcapi import settings
from pcapi.utils import requests
from pcapi.utils.logger import logger

from ..models import MailResult
from .base import BaseBackend


def _add_template_debugging(message_data: dict) -> None:
    message_data["TemplateErrorReporting"] = {
        "Email": settings.DEV_EMAIL_ADDRESS,
        "Name": "Mailjet Template Errors",
    }


class MailjetBackend(BaseBackend):
    def __init__(self):
        super().__init__()
        auth = (settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET)
        self.mailjet_client = MailjetClient(auth=auth, version="v3")

    def _send(self, recipients: Iterable[str], data: dict) -> MailResult:
        data["To"] = ", ".join(recipients)

        if settings.MAILJET_TEMPLATE_DEBUGGING:
            messages_data = data.get("Messages")
            if messages_data:
                for message_data in messages_data:
                    _add_template_debugging(message_data)
            else:
                _add_template_debugging(data)

        try:
            response = self.mailjet_client.send.create(data=data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error trying to send e-mail with Mailjet: %s", exc)
            return MailResult(
                sent_data=data,
                successful=False,
            )

        successful = response.status_code == 200
        if not successful:
            logger.warning("Got %d return code from Mailjet: content=%s", response.status_code, response.content)

        return MailResult(
            sent_data=data,
            successful=successful,
        )

    def create_contact(self, email: str) -> Response:
        data = {"Email": email}
        return self.mailjet_client.contact.create(data=data)

    def update_contact(self, email: str, *, birth_date: datetime.date, department: str) -> Response:
        birth_timestamp = int(datetime.datetime.combine(birth_date, datetime.time(0, 0)).timestamp())

        data = {
            "Data": [
                {"Name": "date_de_naissance", "Value": birth_timestamp},
                {"Name": "département", "Value": department},
            ]
        }
        return self.mailjet_client.contactdata.update(id=email, data=data)

    def add_contact_to_list(self, email: str, list_id: str) -> Response:
        data = {
            "IsUnsubscribed": "false",
            "ContactAlt": email,
            "ListID": list_id,
        }
        return self.mailjet_client.listrecipient.create(data=data)


class ToDevMailjetBackend(MailjetBackend):
    """A backend where the recipients are overriden.

    This is the backend that should be used on testing and staging
    environments.
    """

    def _inject_html_test_notice(self, recipients, data):
        if "Html-part" not in data:
            return
        notice = (
            f"<p>This is a test (ENV={settings.ENV}). "
            f"In production, this email would have been sent to {', '.join(recipients)}</p>"
        )
        data["Html-part"] = notice + data["Html-part"]

    def send_mail(self, recipients: Iterable[str], data: dict) -> MailResult:
        self._inject_html_test_notice(recipients, data)
        recipients = [settings.DEV_EMAIL_ADDRESS]
        return super().send_mail(recipients=recipients, data=data)

    def create_contact(self, email: str) -> Response:
        email = settings.DEV_EMAIL_ADDRESS
        return super().create_contact(email)

    def update_contact(self, email: str, **kwargs) -> Response:
        email = settings.DEV_EMAIL_ADDRESS
        return super().update_contact(email, **kwargs)

    def add_contact_to_list(self, email: str, *args, **kwargs) -> Response:
        email = settings.DEV_EMAIL_ADDRESS
        return super().add_contact_to_list(email, *args, **kwargs)


# Here below we define a custom client for Mailjet that uses our
# `requests` wrapper. This allows automatic logging and a sane default
# timeout. Because Mailjet client code is not very pluggable, this is
# a bit verbose and we need to copy and paste a lot of upstream code.
#  Fortunately, it rarely changes.
class MailjetClient(mailjet_rest.client.Client):
    def __getattr__(self, name):
        # Start of original code.
        # --- 8-> ---
        split = name.split("_")
        # identify the resource
        fname = split[0]
        action = None
        if len(split) > 1:
            # identify the sub resource (action)
            action = split[1]
            if action == "csvdata":
                action = "csvdata/text:plain"
            if action == "csverror":
                action = "csverror/text:csv"
        url, headers = self.config[name]
        # --- 8-> ---
        # Use our `_CustomEndpoint` instead of the original
        # `Endpoint`. This is the only change.
        return type(fname, (_CustomEndpoint,), {})(url=url, headers=headers, action=action, auth=self.auth)


# Here we redefine all methods of the original `Endpoint` class to use
# our `_custom_api_call` instead of the original `api_call`. This is
# the only change.
class _CustomEndpoint(mailjet_rest.client.Endpoint):
    # The original code uses `id` as an argument, which pylint does not like.
    # pylint: disable=redefined-builtin
    def _get(self, filters=None, action_id=None, id=None, **kwargs):
        return _custom_api_call(
            self._auth,
            "get",
            self._url,
            headers=self.headers,
            action=self.action,
            action_id=action_id,
            filters=filters,
            resource_id=id,
            **kwargs,
        )

    def create(self, data=None, filters=None, id=None, action_id=None, **kwargs):
        if self.headers["Content-type"] == "application/json":
            data = json.dumps(data)
        return _custom_api_call(
            self._auth,
            "post",
            self._url,
            headers=self.headers,
            resource_id=id,
            data=data,
            action=self.action,
            action_id=action_id,
            filters=filters,
            **kwargs,
        )

    def update(self, id, data, filters=None, action_id=None, **kwargs):
        if self.headers["Content-type"] == "application/json":
            data = json.dumps(data)
        return _custom_api_call(
            self._auth,
            "put",
            self._url,
            resource_id=id,
            headers=self.headers,
            data=data,
            action=self.action,
            action_id=action_id,
            filters=filters,
            **kwargs,
        )

    def delete(self, id, **kwargs):
        return _custom_api_call(
            self._auth, "delete", self._url, action=self.action, headers=self.headers, resource_id=id, **kwargs
        )


# This is an exact copy of the original `mailjet_rest.client.api_call`,
# but here `requests` is our wrapper, not the original `requests` package.
def _custom_api_call(
    auth,
    method,
    url,
    headers,
    data=None,
    filters=None,
    resource_id=None,
    timeout=60,
    debug=False,
    action=None,
    action_id=None,
    **kwargs,
):
    url = mailjet_rest.client.build_url(url, method=method, action=action, resource_id=resource_id, action_id=action_id)
    req_method = getattr(requests, method)

    try:
        response = req_method(
            url, data=data, params=filters, headers=headers, auth=auth, timeout=timeout, verify=True, stream=False
        )
        return response

    except requests.exceptions.Timeout:
        raise mailjet_rest.client.TimeoutError
    except requests.RequestException as e:
        raise mailjet_rest.client.ApiError(e)
