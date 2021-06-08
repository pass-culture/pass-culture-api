import logging

from pcapi import settings
from pcapi.connectors.api_demarches_simplifiees import get_application_details as get_details
from pcapi.domain.demarches_simplifiees import get_closed_application_ids_for_demarche_simplifiee
from pcapi.models import ImportStatus
from pcapi.models.beneficiary_import import BeneficiaryImport
from pcapi.models.beneficiary_import import BeneficiaryImportSources
from pcapi.repository.beneficiary_import_queries import is_already_imported as already_imported
from pcapi.repository.beneficiary_import_queries import save_beneficiary_import_with_status
from pcapi.repository.user_queries import find_user_by_email as already_existing_user
from pcapi.scripts.beneficiary.remote_import import _process_rejection
from pcapi.scripts.beneficiary.remote_import import parse_beneficiary_information
from pcapi.scripts.beneficiary.remote_import import process_beneficiary_application


logger = logging.getLogger(__name__)


def catchup_with_dms(procedure_id=settings.DMS_ENROLLMENT_PROCEDURE_ID_AFTER_GENERAL_OPENING):
    # Get all applications
    applications_ids = set(get_closed_application_ids_for_demarche_simplifiee(procedure_id, settings.DMS_TOKEN, None))
    # Get processed applications
    existing_applications_id = {
        i[0]
        for i in BeneficiaryImport.query.with_entities(BeneficiaryImport.applicationId)
        .filter(BeneficiaryImport.sourceId == procedure_id)
        .all()
    }
    # Only keep unprocessed applications
    applications_ids = applications_ids - existing_applications_id

    for application_id in applications_ids:
        # Eternal sadness on this not being a function
        # Copied and adapted from pcapi.scripts.beneficiary.remote_import.run
        details = get_details(application_id, procedure_id, settings.DMS_TOKEN)
        try:
            information = parse_beneficiary_information(details)
        except Exception as exc:  # pylint: disable=broad-except
            logger.info(
                "[BATCH][REMOTE IMPORT BENEFICIARIES] Application %s in procedure %s had errors and was ignored: %s",
                application_id,
                procedure_id,
                exc,
                exc_info=True,
            )
            error = f"Le dossier {application_id} contient des erreurs et a été ignoré - Procedure {procedure_id}"
            save_beneficiary_import_with_status(
                ImportStatus.ERROR,
                application_id,
                source=BeneficiaryImportSources.demarches_simplifiees,
                source_id=procedure_id,
                detail=error,
            )
            continue

        user = already_existing_user(information["email"])
        if user and user.isBeneficiary is True:
            _process_rejection(information, procedure_id=procedure_id)
            continue

        if not already_imported(information["application_id"]):
            process_beneficiary_application(
                information=information,
                error_messages=[],
                new_beneficiaries=[],
                retry_ids=[],
                procedure_id=procedure_id,
                preexisting_account=user,
            )
