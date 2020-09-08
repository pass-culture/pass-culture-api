from datetime import datetime
from typing import List

from models import UserSQLEntity, BeneficiaryImport, BeneficiaryImportStatus, ImportStatus
from repository import repository
from workers.beneficiary_job import beneficiary_job


# cas 1
def fix_failed_jobs(application_ids: List[int]):
    for application_id in application_ids:
        beneficiary_job(application_id=application_id)


# cas 2.1.1
def fix_beneficiaries_with_wrong_date_of_birth(date_limit: datetime):
    beneficiaries_from_jouve_with_wrong_birth_date = UserSQLEntity.query \
        .join(BeneficiaryImport) \
        .join(BeneficiaryImportStatus) \
        .filter(BeneficiaryImport.source == 'jouve') \
        .filter(BeneficiaryImportStatus.date <= date_limit) \
        .filter(BeneficiaryImportStatus.status == ImportStatus.CREATED) \
        .all()

    for beneficiary in beneficiaries_from_jouve_with_wrong_birth_date:
        beneficiary_old_date_of_birth = beneficiary.dateOfBirth
        beneficiary.dateOfBirth = datetime(
            year=beneficiary_old_date_of_birth.year,
            month=beneficiary_old_date_of_birth.day,
            day=beneficiary_old_date_of_birth.month
        )
        repository.save(beneficiary)


# cas 2.1.2
def fix_eligible_beneficiaries_who_were_refused(date_limit: datetime):
    beneficiaries_import_from_jouve_to_be_deleted = BeneficiaryImport.query \
        .join(BeneficiaryImportStatus) \
        .filter(BeneficiaryImport.source == 'jouve') \
        .filter(BeneficiaryImportStatus.date <= date_limit) \
        .filter(BeneficiaryImportStatus.status == ImportStatus.REJECTED) \
        .all()

    for beneficiary in beneficiaries_import_from_jouve_to_be_deleted:
        BeneficiaryImportStatus.query.filter(BeneficiaryImportStatus.beneficiaryImportId == beneficiary.id).delete()
        BeneficiaryImport.query.filter(BeneficiaryImport.id == beneficiary.id).delete()
        beneficiary_job(application_id=beneficiary.applicationId)
