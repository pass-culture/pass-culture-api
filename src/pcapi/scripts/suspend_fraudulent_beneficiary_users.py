import logging

from pcapi.core.bookings.repository import find_offers_booked_by_beneficiaries
from pcapi.core.users.api import suspend_account
from pcapi.core.users.constants import SuspensionReason
from pcapi.core.users.models import User
from pcapi.repository.user_queries import find_beneficiary_users_by_email_provider
from pcapi.repository.user_queries import find_user_by_email


logger = logging.getLogger(__name__)


def suspend_fraudulent_beneficiary_users_by_email_providers(
    fraudulent_email_providers: list[str], admin_user_email: str, dry_run: bool = True
) -> dict:
    fraudulent_users = []
    admin_user = find_user_by_email(admin_user_email)

    for email_provider in fraudulent_email_providers:
        fraudulent_users.extend(find_beneficiary_users_by_email_provider(email_provider))
    offers = find_offers_booked_by_beneficiaries(fraudulent_users)

    if not dry_run:
        n_bookings = _suspend_fraudulent_beneficiary_users(fraudulent_users, admin_user)
        logger.info(
            "Fraudulent beneficiaries accounts suspended",
            extra={
                "beneficiaries_suspended_count": len(fraudulent_users),
                "bookings_cancelled_count": n_bookings,
            },
        )
    else:
        n_bookings = -1  # unknown
        logger.info(
            "Dry run results",
            extra={
                "beneficiaries_concerned_count": len(fraudulent_users),
            },
        )
    if len(offers) > 0:
        print(f"Suspended users booked following distinct offers {[offer.id for offer in offers]}")

    return {"fraudulent_users": fraudulent_users, "nb_cancelled_bookings": n_bookings}


def _suspend_fraudulent_beneficiary_users(fraudulent_users: list[User], admin_user: User) -> int:
    n_bookings = 0
    for fraudulent_user in fraudulent_users:
        result = suspend_account(fraudulent_user, SuspensionReason.FRAUD, admin_user)
        n_bookings += result["cancelled_bookings"]
    return n_bookings
