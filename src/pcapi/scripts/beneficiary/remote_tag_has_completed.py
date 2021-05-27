from datetime import datetime
import logging
import re
from typing import Callable
from typing import Optional

from pcapi import settings
from pcapi.connectors.api_demarches_simplifiees import get_application_details
from pcapi.core.users.api import activate_beneficiary
from pcapi.core.users.api import create_reset_password_token
from pcapi.core.users.api import steps_to_become_beneficiary
from pcapi.core.users.constants import RESET_PASSWORD_TOKEN_LIFE_TIME_EXTENDED
from pcapi.core.users.models import User
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription_validator import get_beneficiary_duplicates
from pcapi.domain.demarches_simplifiees import get_received_application_ids_for_demarche_simplifiee
from pcapi.domain.user_activation import create_beneficiary_from_application
from pcapi.domain.user_emails import send_accepted_as_beneficiary_email
from pcapi.domain.user_emails import send_activation_email
from pcapi.models import ApiErrors
from pcapi.models import ImportStatus
from pcapi.models.beneficiary_import import BeneficiaryImportSources
from pcapi.repository import repository
from pcapi.repository.beneficiary_import_queries import save_beneficiary_import_with_status
from pcapi.repository.user_queries import find_user_by_email
from pcapi.utils.mailing import MailServiceException
from pcapi.workers.push_notification_job import update_user_attributes_job


logger = logging.getLogger(__name__)


def run(
    process_applications_updated_after: datetime,
    procedure_id: int,
    get_all_applications_ids: Callable[..., list[int]] = get_received_application_ids_for_demarche_simplifiee,
    get_details: Callable[..., dict] = get_application_details,
    already_existing_user: Callable[..., User] = find_user_by_email,
) -> None:
    received_application_ids = get_all_applications_ids(
        procedure_id, settings.DMS_TOKEN, process_applications_updated_after
    )
    for application_id in received_application_ids:
        details = get_details(application_id, procedure_id, settings.DMS_TOKEN)

        user = already_existing_user(details["dossier"]["email"])

        if user:
            if user.hasCompletedIdCheck:
                logger.info("User has already completed id check", extra={"user": user.id, "procedure": procedure_id})
            if user.isBeneficiary:
                logger.info("User beneficiary", extra={"user": user.id})

            user.hasCompletedIdCheck = True
            repository.save(user)

        else:
            logger.info("No user")


def process_beneficiary_application(
    information: dict,
    error_messages: list[str],
    new_beneficiaries: list[User],
    retry_ids: list[int],
    procedure_id: int,
    preexisting_account: Optional[User] = None,
) -> None:
    duplicate_users = get_beneficiary_duplicates(
        first_name=information["first_name"],
        last_name=information["last_name"],
        date_of_birth=information["birth_date"],
    )

    if not duplicate_users or information["application_id"] in retry_ids:
        _process_creation(
            error_messages, information, new_beneficiaries, procedure_id, preexisting_account=preexisting_account
        )
    else:
        _process_duplication(duplicate_users, error_messages, information, procedure_id)


def parse_beneficiary_information(application_detail: dict) -> dict:
    dossier = application_detail["dossier"]

    information = {
        "last_name": dossier["individual"]["nom"],
        "first_name": dossier["individual"]["prenom"],
        "civility": dossier["individual"]["civilite"],
        "email": dossier["email"],
        "application_id": dossier["id"],
    }

    for field in dossier["champs"]:
        label = field["type_de_champ"]["libelle"]
        value = field["value"]

        if "Veuillez indiquer votre département" in label:
            information["department"] = re.search("^[0-9]{2,3}|[2BbAa]{2}", value).group(0)
        if label == "Quelle est votre date de naissance":
            information["birth_date"] = datetime.strptime(value, "%Y-%m-%d")
        if label == "Quel est votre numéro de téléphone":
            information["phone"] = value
        if label == "Quel est le code postal de votre commune de résidence ?":
            space_free = str(value).strip().replace(" ", "")
            information["postal_code"] = re.search("^[0-9]{5}", space_free).group(0)
        if label == "Veuillez indiquer votre statut":
            information["activity"] = value
        if label == "Quelle est votre adresse de résidence":
            information["address"] = value

    return information


def _process_creation(
    error_messages: list[str],
    information: dict,
    new_beneficiaries: list[User],
    procedure_id: int,
    preexisting_account: Optional[User] = None,
) -> None:
    """
    Create/update a user account and complete the import process.
    Note that a 'user' is not always a beneficiary.
    """
    user = create_beneficiary_from_application(information, user=preexisting_account)
    try:
        repository.save(user)
    except ApiErrors as api_errors:
        logger.warning(
            "[BATCH][REMOTE IMPORT BENEFICIARIES] Could not save application %s, because of error: %s - Procedure %s",
            information["application_id"],
            api_errors,
            procedure_id,
        )
        error_messages.append(str(api_errors))
        return

    logger.info(
        "[BATCH][REMOTE IMPORT BENEFICIARIES] Successfully created user for application %s - Procedure %s",
        information["application_id"],
        procedure_id,
    )

    beneficiary_import = save_beneficiary_import_with_status(
        ImportStatus.CREATED,
        information["application_id"],
        source=BeneficiaryImportSources.demarches_simplifiees,
        source_id=procedure_id,
        user=user,
    )

    if not steps_to_become_beneficiary(user):
        deposit_source = beneficiary_import.get_detailed_source()
        activate_beneficiary(user, deposit_source)

    new_beneficiaries.append(user)
    update_user_attributes_job.delay(user.id)
    try:
        if preexisting_account is None:
            token = create_reset_password_token(user, token_life_time=RESET_PASSWORD_TOKEN_LIFE_TIME_EXTENDED)
            send_activation_email(user, token=token)
        else:
            send_accepted_as_beneficiary_email(user)
    except MailServiceException as mail_service_exception:
        logger.exception(
            "Email send_activation_email failure for application %s - Procedure %s : %s",
            information["application_id"],
            procedure_id,
            mail_service_exception,
        )


def _process_duplication(
    duplicate_users: list[User], error_messages: list[str], information: dict, procedure_id: int
) -> None:
    number_of_beneficiaries = len(duplicate_users)
    duplicate_ids = ", ".join([str(u.id) for u in duplicate_users])
    message = f"{number_of_beneficiaries} utilisateur(s) en doublon {duplicate_ids} pour le dossier {information['application_id']} - Procedure {procedure_id}"
    logger.warning("[BATCH][REMOTE IMPORT BENEFICIARIES] Duplicate beneficiaries found : %s", message)
    error_messages.append(message)
    save_beneficiary_import_with_status(
        ImportStatus.DUPLICATE,
        information["application_id"],
        source=BeneficiaryImportSources.demarches_simplifiees,
        source_id=procedure_id,
        detail=f"Utilisateur en doublon : {duplicate_ids}",
    )


def _process_rejection(information: dict, procedure_id: int) -> None:
    save_beneficiary_import_with_status(
        ImportStatus.REJECTED,
        information["application_id"],
        source=BeneficiaryImportSources.demarches_simplifiees,
        source_id=procedure_id,
        detail="Compte existant avec cet email",
    )
    logger.warning(
        "[BATCH][REMOTE IMPORT BENEFICIARIES] Rejected application %s because of already existing email - Procedure %s",
        information["application_id"],
        procedure_id,
    )
