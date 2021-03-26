import logging
from typing import List

from pcapi.core.bookings.api import cancel_booking_for_fraud
from pcapi.core.bookings.repository import find_cancellable_bookings_by_beneficiaries
from pcapi.core.bookings.repository import find_offers_booked_by_beneficiaries
from pcapi.core.users.api import suspend_account
from pcapi.core.users.constants import SuspensionReason
from pcapi.core.users.models import User
from pcapi.repository.user_queries import find_beneficiary_users_by_email_provider


logger = logging.getLogger(__name__)


def suspend_fraudulent_beneficiary_users_by_email_providers(
    fraudulent_email_providers: List[str], admin_user: User, dry_run: bool = True
) -> None:
    fraudulent_users = []

    for email_provider in fraudulent_email_providers:
        fraudulent_users.extend(find_beneficiary_users_by_email_provider(email_provider))
    offers = find_offers_booked_by_beneficiaries(fraudulent_users)

    if not dry_run:
        suspend_fraudulent_beneficiary_users(fraudulent_users, admin_user)
    else:
        logger.info("Suspension of users from fraudulent email providers %s", len(fraudulent_users))

    if len(offers) > 0:
        print(f"Suspended users booked following distinct offers {[offer.id for offer in offers]}")


def suspend_fraudulent_beneficiary_users(fraudulent_users: List[User], admin_user: User) -> None:
    for fraudulent_user in fraudulent_users:
        suspend_account(fraudulent_user, SuspensionReason.FRAUD, admin_user)


def cancel_bookings_by_fraudulent_beneficiary_users(fraudulent_users: List[User]) -> None:
    bookings_to_cancel = find_cancellable_bookings_by_beneficiaries(fraudulent_users)
    for booking in bookings_to_cancel:
        cancel_booking_for_fraud(booking)
