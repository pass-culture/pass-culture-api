from pcapi.core.beneficiaries import api as beneficiaries_api
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.domain.password import generate_reset_token
from pcapi.domain.password import random_password
from pcapi.models import BeneficiaryImport
from pcapi.models import ImportStatus
from pcapi.models.user_sql_entity import UserSQLEntity
from pcapi.scripts.beneficiary import THIRTY_DAYS_IN_HOURS


def to_model(beneficiary_pre_subscription: BeneficiaryPreSubscription) -> UserSQLEntity:
    beneficiary = UserSQLEntity()

    beneficiary.activity = beneficiary_pre_subscription.activity
    beneficiary.address = beneficiary_pre_subscription.address
    beneficiary.city = beneficiary_pre_subscription.city
    beneficiary.civility = beneficiary_pre_subscription.civility
    beneficiary.dateOfBirth = beneficiary_pre_subscription.date_of_birth
    beneficiary.departementCode = beneficiary_pre_subscription.department_code
    beneficiary.email = beneficiary_pre_subscription.email
    beneficiary.firstName = beneficiary_pre_subscription.first_name
    beneficiary.hasSeenTutorials = False
    beneficiary.isAdmin = False
    beneficiary.lastName = beneficiary_pre_subscription.last_name
    beneficiary.password = random_password()
    beneficiary.phoneNumber = beneficiary_pre_subscription.phone_number
    beneficiary.postalCode = beneficiary_pre_subscription.postal_code
    beneficiary.publicName = beneficiary_pre_subscription.public_name
    beneficiary.isBeneficiary = True

    generate_reset_token(beneficiary, validity_duration_hours=THIRTY_DAYS_IN_HOURS)

    deposit = beneficiaries_api.create_deposit(beneficiary, beneficiary_pre_subscription.deposit_source)
    beneficiary.deposits = [deposit]
    _attach_beneficiary_import(beneficiary, beneficiary_pre_subscription)

    return beneficiary


def _attach_beneficiary_import(
    beneficiary: UserSQLEntity, beneficiary_pre_subscription: BeneficiaryPreSubscription
) -> None:
    beneficiary_import = BeneficiaryImport()

    beneficiary_import.applicationId = beneficiary_pre_subscription.application_id
    beneficiary_import.sourceId = beneficiary_pre_subscription.source_id
    beneficiary_import.source = beneficiary_pre_subscription.source
    beneficiary_import.setStatus(status=ImportStatus.CREATED)

    beneficiary.beneficiaryImports = [beneficiary_import]


def to_rejected_model(beneficiary_pre_subscription: BeneficiaryPreSubscription, detail: str) -> BeneficiaryImport:
    beneficiary_import = BeneficiaryImport()

    beneficiary_import.applicationId = beneficiary_pre_subscription.application_id
    beneficiary_import.sourceId = beneficiary_pre_subscription.source_id
    beneficiary_import.source = beneficiary_pre_subscription.source
    beneficiary_import.setStatus(status=ImportStatus.REJECTED, detail=detail)

    return beneficiary_import
