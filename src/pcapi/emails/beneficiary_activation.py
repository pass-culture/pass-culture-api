from datetime import datetime
from typing import Dict
from urllib.parse import quote
from urllib.parse import urlencode

from dateutil.relativedelta import relativedelta

from pcapi import settings
from pcapi.core.users import models as users_models


def get_activation_email_data(user: users_models.User) -> Dict:
    first_name = user.firstName.capitalize()
    email = user.email
    token = user.resetPasswordToken

    return {
        "Mj-TemplateID": 994771,
        "Mj-TemplateLanguage": True,
        "Vars": {
            "prenom_user": first_name,
            "token": token,
            "email": quote(email),
        },
    }


def get_activation_email_data_for_native(user: users_models.User, token: users_models.Token) -> Dict:
    expiration_timestamp = int(token.expirationDate.timestamp())
    query_string = urlencode({"token": token.value, "expiration_timestamp": expiration_timestamp, "email": user.email})
    email_confirmation_link = f"{settings.NATIVE_APP_URL}/signup-confirmation?{query_string}"
    return {
        "Mj-TemplateID": 2015423,
        "Mj-TemplateLanguage": True,
        "Vars": {
            "nativeAppLink": email_confirmation_link,
            "isEligible": int(user.is_eligible),
            "isMinor": int(user.dateOfBirth + relativedelta(years=18) > datetime.today()),
        },
    }


def get_accepted_as_beneficiary_email_data() -> Dict:
    return {
        "Mj-TemplateID": 2016025,
        "Mj-TemplateLanguage": True,
        "Vars": {},
    }


def get_newly_eligible_user_email_data() -> Dict:
    email_link = f"{settings.NATIVE_APP_URL}/"
    return {
        "Mj-TemplateID": 2030056,
        "Mj-TemplateLanguage": True,
        "Vars": {
            "nativeAppLink": email_link,
        },
    }
