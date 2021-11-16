from datetime import datetime
from typing import Optional

from flask import current_app as app
from redis import Redis
from sentry_sdk import capture_exception

from pcapi import settings
from pcapi.core.users import constants
from pcapi.core.users import exceptions
from pcapi.core.users import repository as users_repository
from pcapi.core.users.models import User
from pcapi.repository import user_queries

from .send import send_user_emails_for_email_change


def request_email_update(user: User, email: str, password: Optional[str]) -> None:
    check_email_update_attempts(user, app.redis_client)
    check_email_address_does_not_exist(email)
    check_user_password(user, password)

    expiration_date = save_email_update_activation_token_counter(user, app.redis_client)
    send_user_emails_for_email_change(user, email, expiration_date)


def check_email_update_attempts(user: User, redis: Redis) -> None:
    update_email_attempts_key = f"update_email_attemps_user_{user.id}"
    count = redis.incr(update_email_attempts_key)

    if count == 1:
        redis.expire(update_email_attempts_key, settings.EMAIL_UPDATE_ATTEMPTS_TTL)

    if count > settings.MAX_EMAIL_UPDATE_ATTEMPTS:
        raise exceptions.EmailUpdateLimitReached()


def save_email_update_activation_token_counter(user: User, redis: Redis) -> datetime:
    """
    Use a dummy counter to find out whether the user already has an
    active token.

    * If the incr command returns 1, there were none. Hence, set a TTL
      (expiration_date, the lifetime of the validation token).
    * If not, raise an error because there is already one.
    """
    key = f"update_email_active_tokens_{user.id}"
    count = redis.incr(key)

    if count > 1:
        raise exceptions.EmailUpdateTokenExists()

    expiration_date = datetime.now() + constants.EMAIL_CHANGE_TOKEN_LIFE_TIME
    redis.expireat(key, expiration_date)

    return expiration_date


def check_user_password(user: User, password: Optional[str]) -> None:
    if not password:
        raise exceptions.EmailUpdateInvalidPassword()

    try:
        users_repository.check_user_and_credentials(user, password)
    except exceptions.InvalidIdentifier as exc:
        raise exceptions.EmailUpdateInvalidPassword() from exc
    except exceptions.UnvalidatedAccount as exc:
        # This should not happen. But, if it did:
        # 1. send the error to sentry
        # 2. raise the same error as above, so the end client
        # can't guess what happened.
        capture_exception(exc)
        raise exceptions.EmailUpdateInvalidPassword() from exc


def check_email_address_does_not_exist(email: str) -> None:
    if user_queries.find_user_by_email(email):
        raise exceptions.EmailExistsError(email)
