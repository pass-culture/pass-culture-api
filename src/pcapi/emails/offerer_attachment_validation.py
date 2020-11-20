from typing import Dict

from pcapi import settings
from pcapi.models import UserOfferer
from pcapi.repository.feature_queries import feature_send_mail_to_users_enabled
from pcapi.repository.offerer_queries import find_first_by_user_offerer_id
from pcapi.repository.user_offerer_queries import find_user_offerer_email
from pcapi.utils.mailing import format_environment_for_email


def retrieve_data_for_offerer_attachment_validation_email(user_offerer: UserOfferer) -> Dict:
    recipient = find_user_offerer_email(user_offerer.id)
    pro_user_email = recipient if feature_send_mail_to_users_enabled() else settings.DEV_EMAIL_ADDRESS
    offerer = find_first_by_user_offerer_id(user_offerer.id)
    environment = format_environment_for_email()

    return {
        "FromEmail": settings.SUPPORT_EMAIL_ADDRESS,
        "MJ-TemplateID": 778756,
        "MJ-TemplateLanguage": True,
        "To": pro_user_email,
        "Vars": {"nom_structure": offerer.name, "env": environment},
    }
