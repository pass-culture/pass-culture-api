from pcapi.repository.user_queries import find_user_by_email

from . import exceptions
from .models import User


def _check_user_and_credentials(user: User, password: str) -> None:
    if not user:
        raise exceptions.InvalidIdentifier()
    if not user.isActive:
        raise exceptions.InvalidIdentifier()
    if not user.isValidated or not user.isEmailValidated:
        raise exceptions.UnvalidatedAccount()
    if not user.checkPassword(password):
        raise exceptions.InvalidPassword()


def get_user_with_credentials(identifier: str, password: str) -> User:
    user = find_user_by_email(identifier)
    _check_user_and_credentials(user, password)
    return user
