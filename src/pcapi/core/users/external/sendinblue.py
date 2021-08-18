import logging

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException as SendinblueApiException

from pcapi import settings
from pcapi.core.users import testing
from pcapi.core.users.models import User
from pcapi.tasks.sendinblue_tasks import UpdateSendinblueContactRequest
from pcapi.tasks.sendinblue_tasks import update_contact_attributes_task


logger = logging.getLogger(__name__)


def update_contact_attributes(user: User):
    attributes = _get_contact_attributes(user)
    update_contact_attributes_task.delay(UpdateSendinblueContactRequest(email=user.email, attributes=attributes))


def make_update_request(payload: UpdateSendinblueContactRequest) -> bool:
    if settings.IS_RUNNING_TESTS:
        testing.sendinblue_requests.append({"email": payload.email, "attributes": payload.attributes})
        return True

    if settings.IS_DEV:
        logger.info(
            "A request to Sendinblue Contact API would be sent for user %s with attributes %s",
            payload.email,
            payload.attributes,
        )
        return True

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.SENDINBLUE_API_KEY
    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    create_contact = sib_api_v3_sdk.CreateContact(
        email=payload.email,
        attributes=payload.attributes,
        list_ids=[settings.SENDINBLUE_YOUNG_CONTACT_LIST_ID],
        update_enabled=True,
    )

    try:
        api_instance.create_contact(create_contact)
        return True

    except SendinblueApiException as e:
        logger.exception("Exception when calling ContactsApi->create_contact: %s\n", e)
        return False


def _get_contact_attributes(user: User):
    return {"FIRSTNAME": user.firstName, "LASTNAME": user.lastName, "IS_BENEFICIARY": user.isBeneficiary}
