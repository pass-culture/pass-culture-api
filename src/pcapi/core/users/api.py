from datetime import date
from datetime import datetime
import secrets
from typing import Dict
from typing import Optional
from typing import Tuple

from jwt import DecodeError
from jwt import ExpiredSignatureError
from jwt import InvalidSignatureError
from jwt import InvalidTokenError

from pcapi import settings
from pcapi.core.bookings.conf import LIMIT_CONFIGURATIONS
from pcapi.core.payments import api as payment_api
from pcapi.core.users import exceptions
from pcapi.core.users.models import Expense
from pcapi.core.users.models import ExpenseDomain
from pcapi.core.users.models import TokenType
from pcapi.core.users.models import User
from pcapi.core.users.models import VOID_FIRST_NAME
from pcapi.core.users.utils import create_jwt_token
from pcapi.core.users.utils import decode_jwt_token
from pcapi.core.users.utils import format_email
from pcapi.domain import user_emails
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.domain.password import generate_reset_token
from pcapi.domain.password import random_password
from pcapi.emails.beneficiary_email_change import build_beneficiary_confirmation_email_change_data
from pcapi.emails.beneficiary_email_change import build_beneficiary_information_email_change_data
from pcapi.models import BeneficiaryImport
from pcapi.models import ImportStatus
from pcapi.models.db import db
from pcapi.models.user_session import UserSession
from pcapi.repository import repository
from pcapi.repository.user_queries import find_user_by_email
from pcapi.scripts.beneficiary import THIRTY_DAYS_IN_HOURS
from pcapi.utils import mailing as mailing_utils
from pcapi.utils.logger import logger
from pcapi.utils.mailing import MailServiceException

from . import constants


def create_email_validation_token(user: User) -> Tuple[str, datetime]:
    return create_jwt_token({"userId": user.id}, TokenType.EMAIL_VALIDATION, constants.EMAIL_VALIDATION_TOKEN_LIFE_TIME)


def create_reset_password_token(user: User) -> Tuple[str, datetime]:
    return create_jwt_token({"userId": user.id}, TokenType.RESET_PASSWORD, constants.RESET_PASSWORD_TOKEN_LIFE_TIME)


def create_id_check_token(user: User) -> Optional[Tuple[str, datetime]]:
    if not is_user_eligible(user):
        return None

    return create_jwt_token({"userId": user.id}, TokenType.ID_CHECK, constants.ID_CHECK_TOKEN_LIFE_TIME)


def create_change_email_token(user: User) -> Tuple[str, datetime]:
    return create_jwt_token({"userId": user.id}, TokenType.RESET_PASSWORD, constants.RESET_PASSWORD_TOKEN_LIFE_TIME)


def create_account(
    email: str,
    password: str,
    birthdate: date,
    has_allowed_recommendations: bool = False,
    is_email_validated: bool = False,
    send_activation_mail: bool = True,
) -> User:
    if find_user_by_email(email):
        raise exceptions.UserAlreadyExistsException()

    user = User(
        email=format_email(email),
        dateOfBirth=datetime.combine(birthdate, datetime.min.time()),
        isEmailValidated=is_email_validated,
        departementCode="007",
        publicName="   ",  # Required because model validation requires 3+ chars
        hasSeenTutorials=False,
        firstName=VOID_FIRST_NAME,
        hasAllowedRecommendations=has_allowed_recommendations,
    )

    age = user.calculate_age()
    if not age or age < constants.ACCOUNT_CREATION_MINIMUM_AGE:
        raise exceptions.UnderAgeUserException()

    user.setPassword(password)
    repository.save(user)

    if not is_email_validated and send_activation_mail:
        request_email_confirmation(user)
    return user


def activate_beneficiary(user: User, deposit_source: str) -> User:
    if not is_user_eligible(user):
        raise exceptions.NotEligible()
    user.isBeneficiary = True
    deposit = payment_api.create_deposit(user, deposit_source=deposit_source)
    db.session.add_all((user, deposit))
    db.session.commit()
    return user


def attach_beneficiary_import_details(
    beneficiary: User, beneficiary_pre_subscription: BeneficiaryPreSubscription
) -> None:
    beneficiary_import = BeneficiaryImport()

    beneficiary_import.applicationId = beneficiary_pre_subscription.application_id
    beneficiary_import.sourceId = beneficiary_pre_subscription.source_id
    beneficiary_import.source = beneficiary_pre_subscription.source
    beneficiary_import.setStatus(status=ImportStatus.CREATED)

    beneficiary.beneficiaryImports = [beneficiary_import]


def request_email_confirmation(user: User) -> None:
    token, expiration_date = create_email_validation_token(user)
    user_emails.send_activation_email(
        user, mailing_utils.send_raw_email, native_version=True, token=token, token_expiration_date=expiration_date
    )


def request_password_reset(user: User) -> None:
    if not user or not user.isActive:
        return

    reset_password_token, expiration_date = create_reset_password_token(user)

    is_email_sent = user_emails.send_reset_password_email_to_native_app_user(
        user.email, reset_password_token, expiration_date, mailing_utils.send_raw_email
    )

    if not is_email_sent:
        logger.error("Email service failure when user requested password reset for email '%s'", user.email)
        raise exceptions.EmailNotSent()


def is_user_eligible(user: User) -> bool:
    age = user.calculate_age()
    return age is not None and age == constants.ELIGIBILITY_AGE


def fulfill_user_data(user: User, deposit_source: str) -> User:
    user.password = random_password()
    generate_reset_token(user, validity_duration_hours=THIRTY_DAYS_IN_HOURS)

    deposit = payment_api.create_deposit(user, deposit_source)
    user.deposits = [deposit]

    return user


def suspend_account(user: User, reason: constants.SuspensionReason, actor: User) -> None:
    user.isActive = False
    user.suspensionReason = str(reason)
    # If we ever unsuspend the account, we'll have to explictly enable
    # isAdmin again. An admin now may not be an admin later.
    user.isAdmin = False
    user.setPassword(secrets.token_urlsafe(30))
    repository.save(user)

    sessions = UserSession.query.filter_by(userId=user.id)
    repository.delete(*sessions)

    logger.info("user=%s has been suspended by actor=%s for reason=%s", user.id, actor.id, reason)


def unsuspend_account(user: User, actor: User) -> None:
    user.isActive = True
    user.suspensionReason = ""
    repository.save(user)

    logger.info("user=%s has been unsuspended by actor=%s", user.id, actor.id)


def send_user_emails_for_email_change(user: User, new_email: str) -> None:
    user_with_new_email = User.query.filter_by(email=new_email).first()
    if user_with_new_email:
        return

    information_data = build_beneficiary_information_email_change_data(user.email, user.firstName)
    information_sucessfully_sent = mailing_utils.send_raw_email(information_data)
    if not information_sucessfully_sent:
        raise MailServiceException()

    link_for_email_change = _build_link_for_email_change(user.email, new_email)
    confirmation_data = build_beneficiary_confirmation_email_change_data(
        user.firstName, link_for_email_change, new_email
    )
    confirmation_sucessfully_sent = mailing_utils.send_raw_email(confirmation_data)
    if not confirmation_sucessfully_sent:
        raise MailServiceException()

    return


def change_user_email(token: str) -> None:
    try:
        jwt_payload = get_payload_from_jwt_token(token, TokenType.CHANGE_EMAIL)
    except (InvalidTokenError, exceptions.InvalidTokenType) as error:
        raise InvalidTokenError() from error

    if not {"new_email", "current_email"} <= set(jwt_payload):
        raise InvalidTokenError()

    new_email = jwt_payload["new_email"]
    if User.query.filter_by(email=new_email).first():
        return

    current_email = jwt_payload["current_email"]
    current_user = User.query.filter_by(email=current_email).first()
    if not current_user:
        return

    current_user.email = new_email
    sessions = UserSession.query.filter_by(userId=current_user.id)
    repository.delete(*sessions)
    repository.save(current_user)

    return


def _build_link_for_email_change(current_email: str, new_email: str) -> str:
    token, expiration_date = create_jwt_token(
        dict(current_email=current_email, new_email=new_email),
        TokenType.CHANGE_EMAIL,
        constants.EMAIL_CHANGE_TOKEN_LIFE_TIME,
    )

    return f"{settings.WEBAPP_URL}/email-change?token={token}&expiration_timestamp={int(expiration_date.timestamp())}"


def user_expenses(user: User):
    version = user.deposit_version

    if not version:
        return []

    bookings = user.get_not_cancelled_bookings()
    config = LIMIT_CONFIGURATIONS[version]

    limits = [
        Expense(
            domain=ExpenseDomain.ALL,
            current=sum(booking.total_amount for booking in bookings),
            limit=config.TOTAL_CAP,
        )
    ]
    if config.DIGITAL_CAP:
        digital_bookings_total = sum(
            [booking.total_amount for booking in bookings if config.digital_cap_applies(booking.stock.offer)]
        )
        limits.append(Expense(domain=ExpenseDomain.DIGITAL, current=digital_bookings_total, limit=config.DIGITAL_CAP))
    if config.PHYSICAL_CAP:
        physical_bookings_total = sum(
            [booking.total_amount for booking in bookings if config.physical_cap_applies(booking.stock.offer)]
        )
        limits.append(
            Expense(
                domain=ExpenseDomain.PHYSICAL,
                current=physical_bookings_total,
                limit=config.PHYSICAL_CAP,
            )
        )

    return limits


def get_payload_from_jwt_token(token: str, expected_token_type: TokenType) -> Dict:
    try:
        token_payload = decode_jwt_token(token)
    except (
        ExpiredSignatureError,
        InvalidSignatureError,
        DecodeError,
        InvalidTokenError,
    ) as error:
        raise InvalidTokenError() from error

    if token_payload["type"] != expected_token_type.value:
        raise exceptions.InvalidTokenType()

    return token_payload


def get_user_from_jwt_token(token: str, expected_token_type: TokenType) -> Optional[User]:
    try:
        token_payload = get_payload_from_jwt_token(token, expected_token_type)
    except (InvalidTokenError, exceptions.InvalidTokenType):
        return None

    if not "userId" in token_payload:
        return None

    return User.query.get(token_payload["userId"])
