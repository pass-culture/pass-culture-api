from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import List
from typing import Optional
from typing import Union

from google.cloud import tasks_v2
import sib_api_v3_sdk
from sib_api_v3_sdk.api.contacts_api import ContactsApi
from sib_api_v3_sdk.rest import ApiException as SendinblueApiException

from pcapi import settings
from pcapi.core.users import testing
from pcapi.core.users.external import UserAttributes
from pcapi.tasks.cloud_task import CloudTaskHttpRequest
from pcapi.tasks.cloud_task import enqueue_task
from pcapi.utils import requests


logger = logging.getLogger(__name__)

SENDINBLUE_CONTACTS_QUEUE_NAME = settings.GCP_SENDINBLUE_CONTACTS_QUEUE_NAME
CONTACT_API_URL = "https://api.sendinblue.com/v3/contacts"


@dataclass
class SendinblueUserUpdateData:
    email: str
    attributes: dict


class SendinblueAttributes(Enum):
    BOOKED_OFFER_CATEGORIES = "BOOKED_OFFER_CATEGORIES"
    BOOKED_OFFER_SUBCATEGORIES = "BOOKED_OFFER_SUBCATEGORIES"
    BOOKING_COUNT = "BOOKING_COUNT"
    CREDIT = "CREDIT"
    DATE_CREATED = "DATE_CREATED"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    DEPARTMENT_CODE = "DEPARTMENT_CODE"
    DEPOSIT_ACTIVATION_DATE = "DEPOSIT_ACTIVATION_DATE"
    DEPOSIT_EXPIRATION_DATE = "DEPOSIT_EXPIRATION_DATE"
    FIRSTNAME = "FIRSTNAME"
    HAS_COMPLETED_ID_CHECK = "HAS_COMPLETED_ID_CHECK"
    INITIAL_CREDIT = "INITIAL_CREDIT"
    IS_BENEFICIARY = "IS_BENEFICIARY"
    IS_ELIGIBLE = "IS_ELIGIBLE"
    IS_EMAIL_VALIDATED = "IS_EMAIL_VALIDATED"
    IS_PRO = "IS_PRO"
    LAST_BOOKING_DATE = "LAST_BOOKING_DATE"
    LAST_FAVORITE_CREATION_DATE = "LAST_FAVORITE_CREATION_DATE"
    LAST_VISIT_DATE = "LAST_VISIT_DATE"
    LASTNAME = "LASTNAME"
    MARKETING_EMAIL_SUBSCRIPTION = "MARKETING_EMAIL_SUBSCRIPTION"
    POSTAL_CODE = "POSTAL_CODE"
    PRODUCT_BRUT_X_USE_DATE = "PRODUCT_BRUT_X_USE_DATE"
    USER_ID = "USER_ID"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


def format_list(raw_list: List[str]) -> str:
    return ",".join(raw_list)


def format_date(date: Optional[datetime]) -> str:
    return date.strftime("%d-%m-%Y") if date else None


def format_user_attributes(user_attributes: UserAttributes) -> dict:
    return {
        SendinblueAttributes.BOOKED_OFFER_CATEGORIES.value: format_list(user_attributes.booking_categories),
        SendinblueAttributes.BOOKED_OFFER_SUBCATEGORIES.value: format_list(user_attributes.booking_subcategories),
        SendinblueAttributes.BOOKING_COUNT.value: user_attributes.booking_count,
        SendinblueAttributes.CREDIT.value: float(user_attributes.domains_credit.all.remaining)
        if user_attributes.domains_credit
        else None,
        SendinblueAttributes.DATE_CREATED.value: format_date(user_attributes.date_created),
        SendinblueAttributes.DATE_OF_BIRTH.value: format_date(user_attributes.date_of_birth),
        SendinblueAttributes.DEPARTMENT_CODE.value: user_attributes.departement_code,
        SendinblueAttributes.DEPOSIT_ACTIVATION_DATE.value: format_date(user_attributes.deposit_activation_date),
        SendinblueAttributes.DEPOSIT_EXPIRATION_DATE.value: format_date(user_attributes.deposit_expiration_date),
        SendinblueAttributes.FIRSTNAME.value: user_attributes.first_name,
        SendinblueAttributes.HAS_COMPLETED_ID_CHECK.value: user_attributes.has_completed_id_check,
        SendinblueAttributes.INITIAL_CREDIT.value: float(user_attributes.domains_credit.all.initial)
        if user_attributes.domains_credit
        else None,
        SendinblueAttributes.IS_BENEFICIARY.value: user_attributes.is_beneficiary,
        SendinblueAttributes.IS_ELIGIBLE.value: user_attributes.is_eligible,
        SendinblueAttributes.IS_EMAIL_VALIDATED.value: user_attributes.is_email_validated,
        SendinblueAttributes.IS_PRO.value: user_attributes.is_pro,
        SendinblueAttributes.LAST_BOOKING_DATE.value: format_date(user_attributes.last_booking_date),
        SendinblueAttributes.LAST_FAVORITE_CREATION_DATE.value: format_date(
            user_attributes.last_favorite_creation_date
        ),
        SendinblueAttributes.LAST_VISIT_DATE.value: format_date(user_attributes.last_visit_date),
        SendinblueAttributes.LASTNAME.value: user_attributes.last_name,
        SendinblueAttributes.MARKETING_EMAIL_SUBSCRIPTION.value: user_attributes.marketing_email_subscription,
        SendinblueAttributes.POSTAL_CODE.value: user_attributes.postal_code,
        SendinblueAttributes.PRODUCT_BRUT_X_USE_DATE.value: format_date(
            user_attributes.products_use_date.get("product_brut_x_use")
        ),
        SendinblueAttributes.USER_ID.value: user_attributes.user_id,
    }


def update_contact_attributes(user_email: str, user_attributes: UserAttributes) -> None:
    formatted_attributes = format_user_attributes(user_attributes)

    constact_list_ids = (
        [settings.SENDINBLUE_PRO_CONTACT_LIST_ID]
        if user_attributes.is_pro
        else [settings.SENDINBLUE_YOUNG_CONTACT_LIST_ID]
    )

    headers = {"Accept": "application/json", "api-key": settings.SENDINBLUE_API_KEY, "Content-Type": "application/json"}
    body = {
        "email": user_email,
        "attributes": formatted_attributes,
        "emailBlacklisted": not user_attributes.marketing_email_subscription,
        "listIds": constact_list_ids,
        "updateEnabled": True,
    }

    if settings.IS_RUNNING_TESTS:
        testing.sendinblue_requests.append({"body": body, "headers": headers})
        return

    if settings.IS_DEV:
        logger.info("A request to Sendinblue Contact API would be sent", extra={"body": body, "headers": headers})
        return

    http_request = CloudTaskHttpRequest(
        http_method=tasks_v2.HttpMethod.POST,
        headers=headers,
        url=CONTACT_API_URL,
        json=body,
    )

    enqueue_task(SENDINBLUE_CONTACTS_QUEUE_NAME, http_request)


# TODO(viconnex): remove this method when the cloud tasks retargetting the api has been leased (27/09/2021)
def make_update_request(email: str, attributes: dict, contact_list_ids: list[int], emailBlacklisted: bool) -> bool:
    headers = {"Accept": "application/json", "api-key": settings.SENDINBLUE_API_KEY, "Content-Type": "application/json"}
    body = {
        "email": email,
        "attributes": attributes,
        "emailBlacklisted": emailBlacklisted,
        "listIds": contact_list_ids,
        "updateEnabled": True,
    }

    try:
        response = requests.post(CONTACT_API_URL, headers=headers, json=body)
    except Exception as exception:  # pylint: disable=broad-except
        logger.exception(
            "Exception when calling ContactsApi->create_contact: %s",
            exception,
            extra={
                "email": email,
                "attributes": attributes,
                "emailBlacklisted": emailBlacklisted,
            },
        )
        return False

    if not response.ok:
        logger.exception(
            "Got %s status code when calling ContactsApi->create_contact with content: %s",
            response.status_code,
            response.content,
            extra={
                "email": email,
                "attributes": attributes,
                "emailBlacklisted": emailBlacklisted,
            },
        )
        return False

    return True


def send_import_contacts_request(
    api_instance: ContactsApi, file_body: str, list_ids: List[int], email_blacklist: bool = False
) -> None:
    request_contact_import = sib_api_v3_sdk.RequestContactImport(
        email_blacklist=email_blacklist,
        sms_blacklist=False,
        update_existing_contacts=True,
        empty_contacts_attributes=False,
    )
    request_contact_import.file_body = file_body
    request_contact_import.list_ids = list_ids

    try:
        api_instance.import_contacts(request_contact_import)
    except SendinblueApiException as e:
        print("Exception when calling ContactsApi->import_contacts: %s" % e)


def format_file_value(value: Optional[Union[str, bool, int, datetime]]) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def build_file_body(users_data: List[SendinblueUserUpdateData]) -> str:
    """Generates a csv-like string for bulk import, based on SendinblueAttributes
       e.g.: "EMAIL;FIRSTNAME;SMS\n#john@example.com;John;Doe;31234567923"

    Args:
        users_data (List[SendinblueUserUpdateData]): users data

    Returns:
        str: corresponding csv string
    """
    file_body = ";".join(sorted(SendinblueAttributes.list())) + ";EMAIL"
    for user in users_data:
        file_body += "\n"
        file_body += ";".join([format_file_value(value) for _, value in sorted(user.attributes.items())])
        file_body += f";{user.email}"

    return file_body


def import_contacts_in_sendinblue(
    sendinblue_users_data: List[SendinblueUserUpdateData], email_blacklist: bool = False
) -> None:
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.SENDINBLUE_API_KEY
    api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Split users in sendinblue lists
    pro_users = [
        user_data for user_data in sendinblue_users_data if user_data.attributes[SendinblueAttributes.IS_PRO.value]
    ]
    young_users = [
        user_data for user_data in sendinblue_users_data if not user_data.attributes[SendinblueAttributes.IS_PRO.value]
    ]

    # send pro users request
    if pro_users:
        pro_users_file_body = build_file_body(pro_users)
        send_import_contacts_request(
            api_instance,
            file_body=pro_users_file_body,
            list_ids=[settings.SENDINBLUE_PRO_CONTACT_LIST_ID],
            email_blacklist=email_blacklist,
        )
    # send young users request
    if young_users:
        young_users_file_body = build_file_body(young_users)
        send_import_contacts_request(
            api_instance,
            file_body=young_users_file_body,
            list_ids=[settings.SENDINBLUE_YOUNG_CONTACT_LIST_ID],
            email_blacklist=email_blacklist,
        )
