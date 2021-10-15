from sqlalchemy import sql

import pcapi.core.payments.conf as bookings_conf
from pcapi.core.payments.models import Deposit
from pcapi.core.payments.models import DepositType
from pcapi.core.users.models import User
from pcapi.models import db
from pcapi.models.payment import Payment
from pcapi.models.payment_status import PaymentStatus
from pcapi.models.payment_status import TransactionStatus

from . import exceptions
from . import repository


def create_deposit(beneficiary: User, deposit_source: str, version: int = None) -> Deposit:
    """Create a new deposit for the user if there is no deposit yet.

    The ``version`` argument MUST NOT be used outside (very specific) tests.
    """
    deposit_type = DepositType.GRANT_18
    existing_deposits = repository.does_deposit_exists_for_beneficiary_and_type(beneficiary, deposit_type)
    if existing_deposits:
        raise exceptions.DepositTypeAlreadyGrantedException(deposit_type)

    if version is None:
        version = bookings_conf.get_current_deposit_version_for_type(deposit_type)
    booking_configuration = bookings_conf.get_limit_configuration_for_type_and_version(deposit_type, version)

    deposit = Deposit(
        version=version,
        type=deposit_type,
        amount=booking_configuration.TOTAL_CAP,
        source=deposit_source,
        user=beneficiary,
        expirationDate=booking_configuration.compute_expiration_date(beneficiary.dateOfBirth),
    )
    return deposit


def bulk_create_payment_statuses(payment_query, status: TransactionStatus, detail=None):
    sel = payment_query.with_entities(Payment.id, sql.literal(status.name), sql.literal(detail))
    query = sql.insert(PaymentStatus).from_select(["paymentId", "status", "detail"], sel)
    db.session.execute(query)
    db.session.commit()
