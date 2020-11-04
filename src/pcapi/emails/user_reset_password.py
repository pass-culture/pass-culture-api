from datetime import datetime
from typing import Dict

from pcapi.models import UserSQLEntity
from pcapi.repository.feature_queries import feature_send_mail_to_users_enabled
from pcapi import settings
from pcapi.utils.mailing import format_environment_for_email


def retrieve_data_for_reset_password_user_email(user: UserSQLEntity) -> Dict:
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


def retrieve_data_for_reset_password_user_native_app_email(user: UserSQLEntity) -> Dict:
    user_email = user.email
    user_reset_password_token = user.resetPasswordToken
    expiration_timestamp = int(datetime.utcnow().timestamp())
    reset_password_link = (
        f"{NATIVE_APP_URL}/mot-de-passe-perdu?token={user_reset_password_token}"
        f"&expiration_timestamp={expiration_timestamp}"
    )

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "MJ-TemplateID": 1838526,
        "MJ-TemplateLanguage": True,
        "To": user_email if feature_send_mail_to_users_enabled() else settings.DEV_EMAIL_ADDRESS,
        "Vars": {"native_app_link": reset_password_link},
    }
