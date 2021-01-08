from datetime import datetime
from typing import Dict

from pcapi import settings
from pcapi.core.users.models import User
from pcapi.repository.feature_queries import feature_send_mail_to_users_enabled
from pcapi.utils.mailing import format_environment_for_email


def retrieve_data_for_reset_password_user_email(user: User) -> Dict:
    user_first_name = user.firstName
    user_email = user.email
    user_reset_password_token = user.resetPasswordToken
    env = format_environment_for_email()

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "MJ-TemplateID": 912168,
        "MJ-TemplateLanguage": True,
        "To": user_email if feature_send_mail_to_users_enabled() else settings.DEV_EMAIL_ADDRESS,
        "Vars": {"prenom_user": user_first_name, "token": user_reset_password_token, "env": env},
    }


def retrieve_data_for_reset_password_native_app_email(
    user_email: str, token_value: str, expiration_date: datetime
) -> Dict:
    reset_password_link = (
        f"{settings.NATIVE_APP_URL}/mot-de-passe-perdu?token={token_value}"
        f"&expiration_timestamp={int(expiration_date.timestamp())}"
        f"&email={user_email}"
    )

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "MJ-TemplateID": 1838526,
        "MJ-TemplateLanguage": True,
        "To": user_email if feature_send_mail_to_users_enabled() else settings.DEV_EMAIL_ADDRESS,
        "Vars": {"native_app_link": reset_password_link},
    }
