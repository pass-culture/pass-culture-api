import pytest

from pcapi.core.users.factories import BeneficiaryImportFactory
from pcapi.core.users.factories import BeneficiaryImportStatusFactory
from pcapi.core.users.factories import UserFactory
from pcapi.core.users.models import User
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.scripts.beneficiary.update_has_completed_idcheck import update_has_completed_idcheck


@pytest.mark.usefixtures("db_session")
def test_update_beneficiary_when_this_dms_account_is_invalid():
    #  Given
    invalid_beneficiary = UserFactory(hasCompletedIdCheck=False)
    invalid_beneficiaryImport = BeneficiaryImportFactory(beneficiary=invalid_beneficiary)
    BeneficiaryImportStatusFactory(
        status=ImportStatus.CREATED.value, beneficiaryImport=invalid_beneficiaryImport, author=invalid_beneficiary
    )

    valid_beneficiary = UserFactory(hasCompletedIdCheck=True)
    valid_beneficiaryImport = BeneficiaryImportFactory(beneficiary=valid_beneficiary)
    BeneficiaryImportStatusFactory(
        status=ImportStatus.CREATED.value, beneficiaryImport=valid_beneficiaryImport, author=valid_beneficiary
    )

    UserFactory(publicName="beneficiary_without_dms_account", hasCompletedIdCheck=False)

    # When
    update_has_completed_idcheck()

    # Then
    assert User.query.filter(User.hasCompletedIdCheck.is_(True)).count() == 2
