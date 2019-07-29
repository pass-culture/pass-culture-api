import os
import re
from datetime import datetime
from typing import Callable, List

from connectors.api_demarches_simplifiees import get_application_details
from domain.admin_emails import send_remote_beneficiaries_import_report_email
from domain.demarches_simplifiees import get_all_application_ids_for_procedure
from domain.user_activation import create_beneficiary_from_application
from domain.user_emails import send_activation_notification_email
from models import ImportStatus
from models import User, ApiErrors, PcObject
from repository.beneficiary_import_queries import is_already_imported, save_beneficiary_import_with_status, \
    find_applications_ids_to_retry
from repository.user_queries import find_by_civility, find_user_by_email
from utils.logger import logger
from utils.mailing import send_raw_email, parse_email_addresses, DEV_EMAIL_ADDRESS

TOKEN = os.environ.get('DEMARCHES_SIMPLIFIEES_TOKEN', None)
PROCEDURE_ID = os.environ.get('DEMARCHES_SIMPLIFIEES_ENROLLMENT_PROCEDURE_ID', None)
VALIDATED_APPLICATION = 'closed'


def run(
        process_applications_updated_after: datetime,
        get_all_applications_ids: Callable[..., List[int]] = get_all_application_ids_for_procedure,
        get_applications_ids_to_retry: Callable[..., List[int]] = find_applications_ids_to_retry,
        get_details: Callable[..., dict] = get_application_details,
        already_imported: Callable[..., bool] = is_already_imported,
        already_existing_user: Callable[..., User] = find_user_by_email
):
    error_messages = []
    new_beneficiaries = []

    logger.info('[BATCH][REMOTE IMPORT BENEFICIARIES] Start import from Démarches Simplifiées')
    applications_ids = get_all_applications_ids(PROCEDURE_ID, TOKEN, process_applications_updated_after)
    retry_ids = get_applications_ids_to_retry()
    logger.info(f'[BATCH][REMOTE IMPORT BENEFICIARIES] {len(applications_ids)} new applications to process')
    logger.info(f'[BATCH][REMOTE IMPORT BENEFICIARIES] {len(retry_ids)} preivous applications to retry')

    for id in (applications_ids + retry_ids):
        details = get_details(id, PROCEDURE_ID, TOKEN)
        try:
            information = parse_beneficiary_information(details)
        except Exception:
            error = f"Le dossier {id} contient des erreurs et a été ignoré"
            logger.error(f'[BATCH][REMOTE IMPORT BENEFICIARIES] {error}')
            error_messages.append(error)
            save_beneficiary_import_with_status(ImportStatus.ERROR, id, detail=error)
            continue

        if already_existing_user(information['email']):
            save_beneficiary_import_with_status(
                ImportStatus.REJECTED,
                information['application_id'],
                detail='Compte existant avec cet email'
            )
            continue

        if not already_imported(information['application_id']):
            process_beneficiary_application(information, error_messages, new_beneficiaries)

    REPORT_RECIPIENTS = os.environ.get('DEMARCHES_SIMPLIFIEES_ENROLLMENT_REPORT_RECIPIENTS', DEV_EMAIL_ADDRESS)
    recipients = parse_email_addresses(REPORT_RECIPIENTS)
    send_remote_beneficiaries_import_report_email(new_beneficiaries, error_messages, recipients, send_raw_email)
    logger.info('[BATCH][REMOTE IMPORT BENEFICIARIES] End import from Démarches Simplifiées')


def process_beneficiary_application(
        information: dict, error_messages: List[str], new_beneficiaries,
        find_duplicate_users: Callable[..., List[User]] = find_by_civility
):
    duplicate_users = find_duplicate_users(
        information['first_name'],
        information['last_name'],
        information['birth_date']
    )

    if duplicate_users:
        number_of_beneficiaries = len(duplicate_users)
        duplicate_ids = ", ".join([str(u.id) for u in duplicate_users])
        message = '%s utilisateur(s) en doublons (%s) pour le dossier %s' % (
            number_of_beneficiaries, duplicate_ids, information['application_id']
        )
        logger.warning(f'[BATCH][REMOTE IMPORT BENEFICIARIES] Duplicate beneficiaries found : {message}')
        error_messages.append(message)
        save_beneficiary_import_with_status(
            ImportStatus.DUPLICATE,
            information['application_id'],
            detail=f"Utilisateur en doublon : {duplicate_ids}"
        )
    else:
        new_beneficiary = create_beneficiary_from_application(information)

        try:
            PcObject.save(new_beneficiary)
        except ApiErrors as e:
            logger.warning(f"[BATCH][REMOTE IMPORT BENEFICIARIES] Could not save application "
                           f"{information['application_id']}, because of error : {str(e)}")
            error_messages.append(str(e))
        else:
            save_beneficiary_import_with_status(
                ImportStatus.CREATED,
                information['application_id'],
                user=new_beneficiary
            )
            new_beneficiaries.append(new_beneficiary)
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
            information['department'] = re.search('^[0-9]{2,3}|[2BbAa]{2}', value).group(0)
        if label == 'Date de naissance':
            information['birth_date'] = datetime.strptime(value, '%Y-%m-%d')
        if label == 'Numéro de téléphone':
            information['phone'] = value
        if label == 'Code postal de votre adresse de résidence':
            space_free = value.strip().replace(' ', '')
            information['postal_code'] = re.search('^[0-9]{5}', space_free).group(0)

    return information


def _find_application_ids_to_process(applications: dict, process_applications_updated_after: datetime):
    processable_applications = filter(lambda a: a['state'] == 'closed', applications['dossiers'])
    recent_applications = filter(
        lambda a: _parse_application_date(a) > process_applications_updated_after,
        processable_applications)
    return {a['id'] for a in recent_applications}


def _parse_application_date(application: dict) -> datetime:
    return datetime.strptime(application['updated_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
