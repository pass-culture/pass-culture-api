import base64
import datetime
import io
import logging
import typing

from PIL import Image
from flask import current_app as app
import pytz
import qrcode
import qrcode.image.svg

from pcapi.connectors import redis
from pcapi.core.bookings import conf
from pcapi.core.bookings.models import Booking
from pcapi.core.bookings.models import BookingCancellationReasons
from pcapi.core.bookings.repository import generate_booking_token
from pcapi.core.offers import repository as offers_repository
from pcapi.core.offers.models import ActivationCode
from pcapi.core.offers.models import Stock
from pcapi.core.users.models import User
from pcapi.domain import user_emails
from pcapi.flask_app import db
from pcapi.models.feature import FeatureToggle
from pcapi.repository import feature_queries
from pcapi.repository import repository
from pcapi.repository import transaction
from pcapi.utils.mailing import MailServiceException
from pcapi.workers.push_notification_job import send_cancel_booking_notification
from pcapi.workers.push_notification_job import update_user_attributes_job
from pcapi.workers.push_notification_job import update_user_bookings_attributes_job
from pcapi.workers.user_emails_job import send_booking_cancellation_emails_to_user_and_offerer_job

from . import validation
from .exceptions import NoActivationCodeAvailable
from .validation import check_activation_is_bookable


logger = logging.getLogger(__name__)

QR_CODE_PASS_CULTURE_VERSION = "v3"
QR_CODE_VERSION = 2
QR_CODE_BOX_SIZE = 5
QR_CODE_BOX_BORDER = 1


def get_available_activation_code(stock: Stock) -> typing.Union[ActivationCode]:
    return next(
        (activationCode for activationCode in stock.activationCodes if check_activation_is_bookable(activationCode)),
        None,
    )


def book_offer(
    beneficiary: User,
    stock_id: int,
    quantity: int,
) -> Booking:
    """
    Return a booking or raise an exception if it's not possible.
    Update a user's credit information on Batch.
    """
    # The call to transaction here ensures we free the FOR UPDATE lock
    # on the stock if validation issues an exception
    with transaction():
        stock = offers_repository.get_and_lock_stock(stock_id=stock_id)
        validation.check_can_book_free_offer(beneficiary, stock)
        validation.check_offer_already_booked(beneficiary, stock.offer)
        validation.check_quantity(stock.offer, quantity)
        validation.check_stock_is_bookable(stock)
        total_amount = quantity * stock.price
        validation.check_expenses_limits(beneficiary, total_amount, stock.offer)

        # FIXME (dbaty, 2020-10-20): if we directly set relations (for
        # example with `booking.user = beneficiary`) instead of foreign keys,
        # the session tries to add the object when `get_user_expenses()`
        # is called because autoflush is enabled. As such, the PostgreSQL
        # exceptions (tooManyBookings and insufficientFunds) may raise at
        # this point and will bubble up. If we want them to be caught, we
        # have to set foreign keys, so that the session is NOT autoflushed
        # in `get_user_expenses` and is only committed in `repository.save()`
        # where exceptions are caught. Since we are using flask-sqlalchemy,
        # I don't think that we should use autoflush, nor should we use
        # the `pcapi.repository.repository` module.
        booking = Booking(
            userId=beneficiary.id,
            stockId=stock.id,
            amount=stock.price,
            quantity=quantity,
            token=generate_booking_token(),
        )

        booking.dateCreated = datetime.datetime.utcnow()
        booking.confirmationDate = compute_confirmation_date(stock.beginningDatetime, booking.dateCreated)
        if stock.offer.isDigital and feature_queries.is_active(FeatureToggle.AUTO_ACTIVATE_DIGITAL_BOOKINGS):
            booking.isUsed = True
            booking.dateUsed = datetime.datetime.utcnow()

        if stock.activationCodes:
            activation_code = get_available_activation_code(stock)
            if activation_code is None:
                raise NoActivationCodeAvailable()

            booking.activationCode = activation_code

        stock.dnBookedQuantity += booking.quantity

        repository.save(booking, stock)

    logger.info(
        "Beneficiary booked an offer",
        extra={
            "actor": beneficiary.id,
            "offer": stock.offerId,
            "stock": stock.id,
            "booking": booking.id,
            "used": booking.isUsed,
        },
    )

    try:
        user_emails.send_booking_recap_emails(booking)
    except MailServiceException as error:
        logger.exception("Could not send booking=%s confirmation email to offerer: %s", booking.id, error)
    try:
        user_emails.send_booking_confirmation_email_to_beneficiary(booking)
    except MailServiceException as error:
        logger.exception("Could not send booking=%s confirmation email to beneficiary: %s", booking.id, error)

    if feature_queries.is_active(FeatureToggle.SYNCHRONIZE_ALGOLIA):
        redis.add_offer_id(client=app.redis_client, offer_id=stock.offerId)

    update_user_bookings_attributes_job.delay(beneficiary.id)

    return booking


def _cancel_booking(booking: Booking, reason: BookingCancellationReasons) -> None:
    """Cancel booking and update a user's credit information on Batch"""
    with transaction():
        stock = offers_repository.get_and_lock_stock(stock_id=booking.stockId)
        db.session.refresh(booking)
        if booking.isCancelled:
            logger.info(
                "Booking was already cancelled",
                extra={
                    "booking": booking.id,
                    "reason": str(reason),
                },
            )
            return
        booking.isCancelled = True
        booking.cancellationReason = reason
        stock.dnBookedQuantity -= booking.quantity
        repository.save(booking, stock)
    logger.info(
        "Booking has been cancelled",
        extra={
            "booking": booking.id,
            "reason": str(reason),
        },
    )

    update_user_attributes_job.delay(booking.user.id)

    if feature_queries.is_active(FeatureToggle.SYNCHRONIZE_ALGOLIA):
        redis.add_offer_id(client=app.redis_client, offer_id=booking.stock.offerId)


def _cancel_bookings_from_stock(stock: Stock, reason: BookingCancellationReasons) -> list[Booking]:
    """
    Cancel multiple bookings and update the users' credit information on Batch.
    """
    deleted_bookings = []
    with transaction():
        stock = offers_repository.get_and_lock_stock(stock_id=stock.id)
        for booking in stock.bookings:
            if not booking.isCancelled and not booking.isUsed:
                booking.isCancelled = True
                booking.cancellationReason = reason
                stock.dnBookedQuantity -= booking.quantity
                deleted_bookings.append(booking)
        repository.save(*deleted_bookings)

    for booking in deleted_bookings:
        update_user_attributes_job.delay(booking.user.id)

    if feature_queries.is_active(FeatureToggle.SYNCHRONIZE_ALGOLIA):
        redis.add_offer_id(client=app.redis_client, offer_id=stock.offerId)

    return deleted_bookings


def cancel_booking_by_beneficiary(user: User, booking: Booking) -> None:
    if not user.isBeneficiary:
        raise RuntimeError("Unexpected call to cancel_booking_by_beneficiary with non-beneficiary user %s" % user)
    validation.check_beneficiary_can_cancel_booking(user, booking)
    _cancel_booking(booking, BookingCancellationReasons.BENEFICIARY)

    send_booking_cancellation_emails_to_user_and_offerer_job.delay(booking.id)


def cancel_booking_by_offerer(booking: Booking) -> None:
    validation.check_booking_can_be_cancelled(booking)
    _cancel_booking(booking, BookingCancellationReasons.OFFERER)
    send_cancel_booking_notification.delay([booking.id])


def cancel_bookings_when_offerer_deletes_stock(stock: Stock) -> list[Booking]:
    return _cancel_bookings_from_stock(stock, BookingCancellationReasons.OFFERER)


def cancel_booking_for_fraud(booking: Booking) -> None:
    validation.check_booking_can_be_cancelled(booking)
    _cancel_booking(booking, BookingCancellationReasons.FRAUD)
    logger.info("Cancelled booking for fraud reason", extra={"booking": booking.id})

    try:
        user_emails.send_booking_cancellation_emails_to_user_and_offerer(booking, booking.cancellationReason)
    except MailServiceException as error:
        logger.exception("Could not send booking=%s cancellation emails to offerer: %s", booking.id, error)


def mark_as_used(booking: Booking, uncancel: bool = False) -> None:
    """Mark a booking as used.

    The ``uncancel`` argument should be provided only if the booking
    has been cancelled by mistake or fraudulently after the offer was
    retrieved (for example, when a beneficiary retrieved a book from a
    library and then cancelled their booking before the library marked
    it as used).
    """
    if booking.isUsed:
        logger.info("Booking was already marked as used", extra={"booking": booking.id})
        return
    # I'm not 100% sure the transaction is required here
    # It is not clear to me wether or not Flask-SQLAlchemy will make
    # a rollback if we raise a validation exception.
    # Since I lock the stock, I really want to make sure the lock is
    # removed ASAP.
    with transaction():
        objects_to_save = [booking]
        if uncancel and booking.isCancelled:
            booking.isCancelled = False
            booking.cancellationReason = None
            stock = offers_repository.get_and_lock_stock(stock_id=booking.stockId)
            stock.dnBookedQuantity += booking.quantity
            objects_to_save.append(stock)
        validation.check_is_usable(booking)
        booking.isUsed = True
        booking.dateUsed = datetime.datetime.utcnow()
        repository.save(*objects_to_save)
    logger.info("Booking was marked as used", extra={"booking": booking.id})


def mark_as_unused(booking: Booking) -> None:
    validation.check_can_be_mark_as_unused(booking)
    booking.isUsed = False
    booking.dateUsed = None
    repository.save(booking)
    logger.info("Booking was marked as unused", extra={"booking": booking.id})


def get_qr_code_data(booking_token: str) -> str:
    return f"PASSCULTURE:{QR_CODE_PASS_CULTURE_VERSION};TOKEN:{booking_token}"


def generate_qr_code(booking_token: str) -> str:
    qr = qrcode.QRCode(
        version=QR_CODE_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=QR_CODE_BOX_SIZE,
        border=QR_CODE_BOX_BORDER,
    )

    qr.add_data(get_qr_code_data(booking_token=booking_token))

    image = qr.make_image(fill_color="black", back_color="white")
    return _convert_image_to_base64(image)


def _convert_image_to_base64(image: Image) -> str:
    image_as_bytes = io.BytesIO()
    image.save(image_as_bytes)
    image_as_base64 = base64.b64encode(image_as_bytes.getvalue())
    return f'data:image/png;base64,{str(image_as_base64, encoding="utf-8")}'


def compute_confirmation_date(
    event_beginning: typing.Optional[datetime.datetime], booking_creation_or_event_edition: datetime.datetime
) -> typing.Optional[datetime.datetime]:
    if event_beginning:
        if event_beginning.tzinfo:
            tz_naive_event_beginning = event_beginning.astimezone(pytz.utc)
            tz_naive_event_beginning = tz_naive_event_beginning.replace(tzinfo=None)
        else:
            tz_naive_event_beginning = event_beginning
        before_event_limit = tz_naive_event_beginning - conf.CONFIRM_BOOKING_BEFORE_EVENT_DELAY
        after_booking_or_event_edition_limit = (
            booking_creation_or_event_edition + conf.CONFIRM_BOOKING_AFTER_CREATION_DELAY
        )
        earliest_date_in_cancellation_period = min(before_event_limit, after_booking_or_event_edition_limit)
        latest_date_between_earliest_date_in_cancellation_period_and_booking_creation_or_event_edition = max(
            earliest_date_in_cancellation_period, booking_creation_or_event_edition
        )
        return latest_date_between_earliest_date_in_cancellation_period_and_booking_creation_or_event_edition
    return None


def update_confirmation_dates(
    bookings_to_update: list[Booking], new_beginning_datetime: datetime.datetime
) -> list[Booking]:
    for booking in bookings_to_update:
        booking.confirmationDate = compute_confirmation_date(
            event_beginning=new_beginning_datetime, booking_creation_or_event_edition=datetime.datetime.utcnow()
        )
    repository.save(*bookings_to_update)
    return bookings_to_update


def recompute_dnBookedQuantity(stock_ids: list[int]) -> None:
    query = """
      WITH bookings_per_stock AS (
        SELECT
          stock.id AS stock_id,
          COALESCE(SUM(booking.quantity), 0) AS total_bookings
        FROM stock
        -- The `NOT isCancelled` condition MUST be part of the JOIN.
        -- If it were part of the WHERE clause, that would exclude
        -- stocks that only have cancelled bookings.
        LEFT OUTER JOIN booking
          ON booking."stockId" = stock.id
          AND NOT booking."isCancelled"
        WHERE stock.id IN :stock_ids
        GROUP BY stock.id
      )
      UPDATE stock
      SET "dnBookedQuantity" = bookings_per_stock.total_bookings
      FROM bookings_per_stock
      WHERE stock.id = bookings_per_stock.stock_id
    """
    db.session.execute(query, {"stock_ids": tuple(stock_ids)})
