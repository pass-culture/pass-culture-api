from typing import Dict

from models import UserOfferer
from repository.feature_queries import feature_send_mail_to_users_enabled
from repository.offerer_queries import find_first_by_user_offerer_id
from repository.user_offerer_queries import find_user_offerer_email
from utils.mailing import SUPPORT_EMAIL_ADDRESS, DEV_EMAIL_ADDRESS, format_environment_for_email

def retrieve_data_for_pro_offerer_attachment_validation_email(user_offerer: UserOfferer, ) -> Dict:
    recipient =  find_user_offerer_email(user_offerer.id)
    pro_user_email = recipient if feature_send_mail_to_users_enabled() else DEV_EMAIL_ADDRESS
    offerer = find_first_by_user_offerer_id(user_offerer.id)
    environment = format_environment_for_email()

    return {
        'FromEmail': SUPPORT_EMAIL_ADDRESS,
        'MJ-TemplateID': 778756,
        'MJ-TemplateLanguage': True,
        'To': pro_user_email,
        'Vars': {
            'nom_structure': offerer.name,
            'env': environment
        },
    }

