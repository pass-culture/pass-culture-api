from datetime import datetime
import logging
from typing import Optional

from google.cloud.storage import Client
from google.cloud.storage.bucket import Bucket
import jwt
import phonenumbers
from phonenumbers import PhoneNumber
from phonenumbers.phonenumberutil import NumberParseException

from pcapi import settings
from pcapi.core.users.constants import METROPOLE_PHONE_PREFIX
from pcapi.core.users.constants import PHONE_PREFIX_BY_DEPARTEMENT_CODE
from pcapi.core.users.exceptions import InvalidPhoneNumber
from pcapi.core.users.exceptions import UserWithoutPhoneNumberException
from pcapi.core.users.models import ALGORITHM_HS_256
from pcapi.core.users.models import User
from pcapi.domain.postal_code.postal_code import PostalCode


logger = logging.getLogger(__name__)


def encode_jwt_payload(token_payload: dict, expiration_date: Optional[datetime] = None) -> str:
    if expiration_date:
        # do not fill exp key if expiration_date is None or jwt.decode would fail
        token_payload["exp"] = int(expiration_date.timestamp())

    return jwt.encode(
        token_payload,
        settings.JWT_SECRET_KEY,  # type: ignore # known as str in build assertion
        algorithm=ALGORITHM_HS_256,
    ).decode("ascii")


def decode_jwt_token(jwt_token: str) -> dict:
    return jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)  # type: ignore # known as str in build assertion


def sanitize_email(email: str) -> str:
    return email.strip().lower()


def build_internationalized_phone_number(user: User, phone_number: str) -> str:
    country_code = PHONE_PREFIX_BY_DEPARTEMENT_CODE.get(user.departementCode, METROPOLE_PHONE_PREFIX)
    return country_code + phone_number[1:]


def format_phone_number_with_country_code(user: User) -> str:
    if not user.phoneNumber:
        raise UserWithoutPhoneNumberException()

    if not user.postalCode or (
        PostalCode(user.postalCode)._is_overseas_departement()
        and user.departementCode not in PHONE_PREFIX_BY_DEPARTEMENT_CODE
    ):
        logger.warning(
            "Unknown phone prefix for user %s",
            user,
            extra={"departementCode": user.departementCode, "postalCode": user.postalCode},
        )

    return build_internationalized_phone_number(user, user.phoneNumber)


def parse_phone_number(phone_number: Optional[str]) -> PhoneNumber:
    """
    Phone number must be correctly formatted in international format (E.164)
    and be valid (number of digits, digit sequence)

    Raises:
        InvalidPhoneNumber
    """
    try:
        parsed_phone_number = phonenumbers.parse(phone_number)
    except NumberParseException as error:
        raise InvalidPhoneNumber(str(phone_number)) from error
    except TypeError as error:
        raise InvalidPhoneNumber(str(phone_number)) from error

    if not phonenumbers.is_valid_number(parsed_phone_number):
        raise InvalidPhoneNumber(str(phone_number))

    return parsed_phone_number


def get_formatted_phone_number(phone_number: PhoneNumber) -> str:
    return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)


def get_encrypted_gcp_storage_client_bucket() -> Bucket:
    if not hasattr(get_encrypted_gcp_storage_client_bucket, "client"):
        get_encrypted_gcp_storage_client_bucket.client = Client(project=settings.GCP_PROJECT)

    return get_encrypted_gcp_storage_client_bucket.client.bucket(settings.GCP_BUCKET_NAME)


def store_public_object(
    bucket: str, object_id: str, blob: bytes, content_type: Optional[str] = None, metadata: Optional[dict] = None
) -> None:
    storage_path = bucket + "/" + object_id
    try:
        storage_client_bucket = get_encrypted_gcp_storage_client_bucket()
        gcp_cloud_blob = storage_client_bucket.blob(storage_path)
        gcp_cloud_blob.metadata = metadata
        gcp_cloud_blob.upload_from_string(blob, content_type=content_type)
    except Exception as exception:
        logger.exception("An error has occured while trying to upload file on encrypted GCP bucket: %s", exception)
        raise exception


def delete_public_object(bucket: str, object_id: str) -> None:
    storage_path = bucket + "/" + object_id
    try:
        storage_client_bucket = get_encrypted_gcp_storage_client_bucket()
        gcp_cloud_blob = storage_client_bucket.blob(storage_path)
        gcp_cloud_blob.delete()
    except Exception as exception:
        logger.exception("An error has occured while trying to delete file on encrypted GCP bucket: %s", exception)
        raise exception
