from typing import Dict
from urllib.parse import quote

from pcapi import settings
from pcapi.core.users import models
from pcapi.models import UserSQLEntity
from pcapi.repository.feature_queries import feature_send_mail_to_users_enabled
from pcapi.utils.mailing import format_environment_for_email


def get_activation_email_data(user: UserSQLEntity) -> Dict:
    first_name = user.firstName.capitalize()
    email = user.email
    token = user.resetPasswordToken
    env = format_environment_for_email()

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "Mj-TemplateID": 994771,
        "Mj-TemplateLanguage": True,
        "To": email,
        "Vars": {"prenom_user": first_name, "token": token, "email": quote(email), "env": env},
    }


def get_activation_email_data_for_native(user: UserSQLEntity, token: models.Token) -> Dict:
    expiration_timestamp = int(token.expirationDate.timestamp())
    email_confirmation_link = (
        f"{settings.NATIVE_APP_URL}/email-confirmation?token={token.value}&expiration_timestamp={expiration_timestamp}"
    )
    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "Mj-TemplateID": 1897370,
        "Mj-TemplateLanguage": True,
        "To": user.email if feature_send_mail_to_users_enabled() else settings.DEV_EMAIL_ADDRESS,
        "Vars": {
            "native_app_link": email_confirmation_link,
        },
    }
