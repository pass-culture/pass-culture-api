from datetime import datetime
from typing import List

from models import UserSQLEntity, BeneficiaryImport, BeneficiaryImportStatus, ImportStatus
from repository import repository
from utils.logger import logger
from workers.beneficiary_job import beneficiary_job


# cas 1
def fix_failed_jobs(application_ids: List[int]):
    errors = []
    for application_id in application_ids:
        try:
            beneficiary_job(application_id=application_id)
        except Exception:
            errors.append(application_id)
    logger.info(f'[JOUVE IMPORT CASE 1] application ids in error {errors}')


# cas 2.1.1
def fix_beneficiaries_with_wrong_date_of_birth(date_limit: datetime):
    beneficiaries_from_jouve_with_wrong_birth_date = UserSQLEntity.query \
        .join(BeneficiaryImport) \
        .join(BeneficiaryImportStatus) \
        .filter(BeneficiaryImport.source == 'jouve') \
        .filter(BeneficiaryImportStatus.date <= date_limit) \
        .filter(BeneficiaryImportStatus.status == ImportStatus.CREATED) \
        .all()

    beneficiary_ids = [b.id for b in beneficiaries_from_jouve_with_wrong_birth_date]
    logger.info(f'[JOUVE IMPORT CASE 2.1.1] ids of users to update {beneficiary_ids}')
    for beneficiary in beneficiaries_from_jouve_with_wrong_birth_date:
        beneficiary_old_date_of_birth = beneficiary.dateOfBirth
        beneficiary.dateOfBirth = datetime(
            year=beneficiary_old_date_of_birth.year,
            month=beneficiary_old_date_of_birth.day,
            day=beneficiary_old_date_of_birth.month
        )
        logger.info(f'[JOUVE IMPORT CASE 2.1.1] birthdate of user with {beneficiary.id} was updated')
        repository.save(beneficiary)


# cas 2.1.2
def fix_eligible_beneficiaries_who_were_refused(date_limit: datetime):
    beneficiaries_import_from_jouve_to_be_deleted = BeneficiaryImport.query \
        .join(BeneficiaryImportStatus) \
        .filter(BeneficiaryImport.source == 'jouve') \
        .filter(BeneficiaryImportStatus.date <= date_limit) \
        .filter(BeneficiaryImportStatus.status == ImportStatus.REJECTED) \
        .all()

    beneficiary_import_ids = [b.id for b in beneficiaries_import_from_jouve_to_be_deleted]
    errors = []
    logger.info(f'[JOUVE IMPORT CASE 2.1.2] Beneficiary imports to be deleted {beneficiary_import_ids}')
    for beneficiary_import in beneficiaries_import_from_jouve_to_be_deleted:
        BeneficiaryImportStatus.query.filter(BeneficiaryImportStatus.beneficiaryImportId == beneficiary_import.id).delete()
        BeneficiaryImport.query.filter(BeneficiaryImport.id == beneficiary_import.id).delete()

        try:
            beneficiary_job(application_id=beneficiary_import.applicationId)
        except Exception:
            errors.append(beneficiary_import.applicationId)
    logger.info(f'[JOUVE IMPORT CASE 2.1.2] application ids in error {errors}')
