from pcapi.core.payments import api as payments_api
from pcapi.core.users.models import User
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.domain.password import generate_reset_token
from pcapi.domain.password import random_password
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.scripts.beneficiary import THIRTY_DAYS_IN_HOURS


IMPORT_STATUS_MODIFICATION_RULE = (
    "Seuls les dossiers au statut DUPLICATE peuvent être modifiés (aux statuts REJECTED ou RETRY uniquement)"
)


def create_beneficiary_from_application(beneficiary_pre_subscription: BeneficiaryPreSubscription) -> User:
    beneficiary = User()
    beneficiary.lastName = beneficiary_pre_subscription.last_name
    beneficiary.firstName = beneficiary_pre_subscription.first_name
    beneficiary.publicName = beneficiary_pre_subscription.public_name
    beneficiary.email = beneficiary_pre_subscription.email
    beneficiary.phoneNumber = beneficiary_pre_subscription.phone_number
    beneficiary.departementCode = beneficiary_pre_subscription.department_code
    beneficiary.postalCode = beneficiary_pre_subscription.postal_code
    beneficiary.dateOfBirth = beneficiary_pre_subscription.date_of_birth
    beneficiary.civility = beneficiary_pre_subscription.civility
    beneficiary.activity = beneficiary_pre_subscription.activity
    beneficiary.isBeneficiary = True
    beneficiary.isAdmin = False
    beneficiary.password = random_password()
    beneficiary.hasSeenTutorials = False
    generate_reset_token(beneficiary, validity_duration_hours=THIRTY_DAYS_IN_HOURS)

    deposit = payments_api.create_deposit(beneficiary, beneficiary_pre_subscription.deposit_source)
    beneficiary.deposits = [deposit]

    return beneficiary


def is_import_status_change_allowed(current_status: ImportStatus, new_status: ImportStatus) -> bool:
    if current_status == ImportStatus.DUPLICATE:
        if new_status in (ImportStatus.REJECTED, ImportStatus.RETRY):
            return True
    return False
