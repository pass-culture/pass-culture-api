from typing import List

from sqlalchemy import asc

from pcapi.models import BeneficiaryImport
from pcapi.models import ImportStatus
from pcapi.models.db import db


def is_already_imported(application_id: int) -> bool:
    beneficiary_import = BeneficiaryImport.query.filter(BeneficiaryImport.applicationId == application_id).first()

    if beneficiary_import is None:
        return False

    return beneficiary_import.currentStatus != ImportStatus.RETRY


def find_applications_ids_to_retry() -> List[int]:
    ids = (
        db.session.query(BeneficiaryImport.applicationId)
        .filter(BeneficiaryImport.currentStatus == ImportStatus.RETRY)
        .order_by(asc(BeneficiaryImport.applicationId))
        .all()
    )

    return sorted(list(map(lambda result_set: result_set[0], ids)))
