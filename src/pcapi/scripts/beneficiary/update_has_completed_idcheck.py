from pcapi.repository import repository
from pcapi.repository.user_queries import find_beneficiaries_with_dms_account


def update_has_completed_idcheck() -> None:
    for beneficiary in find_beneficiaries_with_dms_account():
        beneficiary.hasCompletedIdCheck = True
        repository.save(beneficiary)
