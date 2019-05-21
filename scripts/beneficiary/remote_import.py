import os
import re
from datetime import datetime
from typing import Callable, List

from connectors.api_demarches_simplifiees import get_all_applications_for_procedure, get_application_details
from domain.admin_emails import send_remote_beneficiaries_import_report_email
from domain.password import generate_reset_token, random_password
from domain.user_emails import send_activation_notification_email
from models import User, PcObject, Deposit
from repository.user_queries import find_by_first_and_last_names_and_birth_date
from scripts.beneficiary import THIRTY_DAYS_IN_HOURS
from utils.mailing import send_raw_email

TOKEN = os.environ.get('DEMARCHES_SIMPLIFIEES_TOKEN', None)
PROCEDURE_ID = os.environ.get('DEMARCHES_SIMPLIFIEES_ENROLLMENT_PROCEDURE_ID', None)
VALIDATED_APPLICATION = 'closed'


def run(
        get_all_applications: Callable[..., dict] = get_all_applications_for_procedure,
        get_details: Callable[..., dict] = get_application_details,
        find_duplicate_users: Callable[..., User] = find_by_first_and_last_names_and_birth_date
):
    current_page = 1
    number_of_pages = 1
    error_messages = []
    new_beneficiaries = []

    while current_page <= number_of_pages:

        applications = get_all_applications(PROCEDURE_ID, TOKEN, page=current_page)
        current_page, number_of_pages = _handle_pagination(applications, current_page)
        ids_to_process = _find_application_ids_to_process(applications)

        for id in ids_to_process:
            details = get_details(id, PROCEDURE_ID, TOKEN)
            information = parse_beneficiary_information(details)
            process_beneficiary_application(information, error_messages, new_beneficiaries,
                                            find_duplicate_users=find_duplicate_users)

    send_remote_beneficiaries_import_report_email(new_beneficiaries, error_messages, send_raw_email)


class DuplicateBeneficiaryError(Exception):
    def __init__(self, application_id: int, duplicate_beneficiaries: List[User]):
        number_of_beneficiaries = len(duplicate_beneficiaries)
        duplicate_ids = ", ".join([str(u.id) for u in duplicate_beneficiaries])
        self.message = '%s utilisateur(s) en doublons (%s) pour le dossier %s' % (
            number_of_beneficiaries, duplicate_ids, application_id
        )


def process_beneficiary_application(
        information: dict, error_messages: List[str], new_beneficiaries,
        find_duplicate_users: Callable[[str, str, str], User] = find_by_first_and_last_names_and_birth_date
):
    try:
        new_beneficiary = create_beneficiary_from_application(information, find_duplicate_users=find_duplicate_users)
    except DuplicateBeneficiaryError as e:
        error_messages.append(e.message)
    else:
        new_beneficiaries.append(new_beneficiary)
        PcObject.check_and_save(new_beneficiary)
        send_activation_notification_email(new_beneficiary, send_raw_email)


def parse_beneficiary_information(application_detail: dict) -> dict:
    dossier = application_detail['dossier']

    information = {
        'last_name': dossier['individual']['nom'],
        'first_name': dossier['individual']['prenom'],
        'email': dossier['email'],
        'application_id': dossier['id']
    }

    for field in dossier['champs']:
        label = field['type_de_champ']['libelle']
        value = field['value']

        if label == 'Veuillez indiquer votre département':
            information['department'] = re.search('^[0-9]{2}', value).group(0)
        if label == 'Date de naissance':
            information['birth_date'] = datetime.strptime(value, '%Y-%m-%d')
        if label == 'Numéro de téléphone':
            information['phone'] = value
        if label == 'Code postal':
            information['postal_code'] = value

    return information


def create_beneficiary_from_application(
        application_detail: dict,
        find_duplicate_users: Callable[[str, str, str], User] = find_by_first_and_last_names_and_birth_date
) -> User:
    duplicate_users = find_duplicate_users(
        application_detail['first_name'],
        application_detail['last_name'],
        application_detail['birth_date']
    )

    if duplicate_users:
        raise DuplicateBeneficiaryError(application_detail['application_id'], duplicate_users)

    beneficiary = User()
    beneficiary.lastName = application_detail['last_name']
    beneficiary.firstName = application_detail['first_name']
    beneficiary.publicName = '%s %s' % (application_detail['first_name'], application_detail['last_name'])
    beneficiary.email = application_detail['email']
    beneficiary.phoneNumber = application_detail['phone']
    beneficiary.departementCode = application_detail['department']
    beneficiary.postalCode = application_detail['postal_code']
    beneficiary.dateOfBirth = application_detail['birth_date']
    beneficiary.canBookFreeOffers = True
    beneficiary.isAdmin = False
    beneficiary.password = random_password()
    generate_reset_token(beneficiary, validity_duration_hours=THIRTY_DAYS_IN_HOURS)

    deposit = Deposit()
    deposit.amount = 500
    deposit.source = 'démarches simplifiées dossier [%s]' % application_detail['application_id']
    beneficiary.deposits = [deposit]

    return beneficiary


def _find_application_ids_to_process(applications):
    processable_application = filter(lambda a: a['state'] == 'closed', applications['dossiers'])
    ids_to_process = {a['id'] for a in processable_application}
    return ids_to_process


def _handle_pagination(applications, current_page):
    number_of_pages = applications['pagination']['nombre_de_page']
    new_page = current_page + 1
    return new_page, number_of_pages
