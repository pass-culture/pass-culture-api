from datetime import date
from datetime import datetime
from datetime import time
import math
from typing import Optional

from dateutil import tz
from sqlalchemy import Date
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import text
from sqlalchemy.orm import Query
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.util._collections import AbstractKeyedTuple

from pcapi.core.bookings import conf
from pcapi.core.bookings.models import BookingCancellationReasons
from pcapi.core.offerers.models import Offerer
from pcapi.core.users.models import User
from pcapi.core.users.utils import sanitize_email
from pcapi.domain.booking_recap.booking_recap import BookBookingRecap
from pcapi.domain.booking_recap.booking_recap import BookingRecap
from pcapi.domain.booking_recap.booking_recap import EventBookingRecap
from pcapi.domain.booking_recap.booking_recap import ThingBookingRecap
from pcapi.domain.booking_recap.bookings_recap_paginated import BookingsRecapPaginated
from pcapi.domain.postal_code.postal_code import PostalCode
from pcapi.models import Booking
from pcapi.models import Offer
from pcapi.models import Stock
from pcapi.models import UserOfferer
from pcapi.models import Venue
from pcapi.models.api_errors import ResourceNotFoundError
from pcapi.models.db import db
from pcapi.models.payment import Payment
from pcapi.models.payment_status import TransactionStatus
from pcapi.utils.date import get_department_timezone
from pcapi.utils.token import random_token


DUO_QUANTITY = 2


def find_by(token: str, email: str = None, offer_id: int = None) -> Booking:
    query = Booking.query.filter_by(token=token.upper())

    if email:
        # FIXME (dbaty, 2021-05-02): remove call to `func.lower()` once
        # all emails have been sanitized in the database.
        query = query.join(User).filter(func.lower(User.email) == sanitize_email(email))

    if offer_id:
        query_offer = Booking.query.join(Stock).join(Offer).filter_by(id=offer_id)
        query = query.intersect_all(query_offer)

    booking = query.one_or_none()

    if booking is None:
        errors = ResourceNotFoundError()
        errors.add_error("global", "Cette contremarque n'a pas été trouvée")
        raise errors

    return booking


def find_by_pro_user_id(
    user_id: int,
    event_date: Optional[date] = None,
    venue_id: Optional[int] = None,
    page: int = 1,
    per_page_limit: int = 1000,
) -> BookingsRecapPaginated:
    bookings_recap_query = _build_bookings_recap_query(user_id, event_date, venue_id)
    bookings_recap_query_with_duplicates = _duplicate_booking_when_quantity_is_two(bookings_recap_query)

    if page == 1:
        total_bookings_recap = bookings_recap_query_with_duplicates.count()
    else:
        total_bookings_recap = 0

    paginated_bookings = (
        bookings_recap_query_with_duplicates.order_by(text('"bookingDate" DESC'))
        .offset((page - 1) * per_page_limit)
        .limit(per_page_limit)
        .all()
    )

    return _paginated_bookings_sql_entities_to_bookings_recap(
        paginated_bookings=paginated_bookings,
        page=page,
        per_page_limit=per_page_limit,
        total_bookings_recap=total_bookings_recap,
    )


def find_ongoing_bookings_by_stock(stock_id: int) -> list[Booking]:
    return Booking.query.filter_by(stockId=stock_id, isCancelled=False, isUsed=False).all()


def find_not_cancelled_bookings_by_stock(stock: Stock) -> list[Booking]:
    return Booking.query.filter_by(stockId=stock.id, isCancelled=False).all()


def find_bookings_eligible_for_payment_for_venue(venue_id: int) -> list[Booking]:
    return (
        _find_bookings_eligible_for_payment()
        .filter(Venue.id == venue_id)
        .reset_joinpoint()
        .outerjoin(Payment)
        .options(joinedload(Booking.stock).joinedload(Stock.offer).joinedload(Offer.product))
        .options(joinedload(Booking.stock).joinedload(Stock.offer).joinedload(Offer.venue))
        .options(
            joinedload(Booking.stock).joinedload(Stock.offer).joinedload(Offer.venue).joinedload(Venue.bankInformation)
        )
        .options(
            joinedload(Booking.stock)
            .joinedload(Stock.offer)
            .joinedload(Offer.venue)
            .joinedload(Venue.managingOfferer)
            .joinedload(Offerer.bankInformation)
        )
        .options(joinedload(Booking.payments))
        .order_by(Payment.id, Booking.dateCreated.asc())
        .all()
    )


def token_exists(token: str) -> bool:
    return db.session.query(Booking.query.filter_by(token=token.upper()).exists()).scalar()


def find_not_used_and_not_cancelled() -> list[Booking]:
    return Booking.query.filter(Booking.isUsed.is_(False)).filter(Booking.isCancelled.is_(False)).all()


def find_used_by_token(token: str) -> Booking:
    return Booking.query.filter_by(token=token.upper(), isUsed=True).one_or_none()


def count_not_cancelled_bookings_quantity_by_stock_id(stock_id: int) -> int:
    bookings = (
        Booking.query.join(Stock).filter(Booking.isCancelled.is_(False)).filter(Booking.stockId == stock_id).all()
    )

    return sum([booking.quantity for booking in bookings])


def find_expiring_bookings() -> Query:
    today_at_midnight = datetime.combine(date.today(), time(0, 0))
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .filter(
            ~Booking.isCancelled,
            ~Booking.isUsed,
            (Booking.dateCreated + conf.BOOKINGS_AUTO_EXPIRY_DELAY) <= today_at_midnight,
            Offer.canExpire,
        )
    )


def find_expiring_bookings_ids() -> Query:
    return find_expiring_bookings().order_by(Booking.id).with_entities(Booking.id)


def find_soon_to_be_expiring_booking_ordered_by_user(given_date: date = None) -> Query:
    given_date = given_date or date.today()
    given_date = datetime.combine(given_date, time(0, 0)) + conf.BOOKINGS_EXPIRY_NOTIFICATION_DELAY
    window = (datetime.combine(given_date, time(0, 0)), datetime.combine(given_date, time(23, 59, 59)))

    return (
        Booking.query.join(Stock)
        .join(Offer)
        .filter(
            ~Booking.isCancelled,
            ~Booking.isUsed,
            (Booking.dateCreated + conf.BOOKINGS_AUTO_EXPIRY_DELAY).between(*window),
            Offer.canExpire,
        )
        .order_by(Booking.userId)
    )


def generate_booking_token():
    for _i in range(100):
        token = random_token()
        if not token_exists(token):
            return token
    raise ValueError("Could not generate new booking token")


def find_expired_bookings_ordered_by_user(expired_on: date = None) -> Query:
    expired_on = expired_on or date.today()
    return (
        Booking.query.filter(Booking.isCancelled.is_(True))
        .filter(cast(Booking.cancellationDate, Date) == expired_on)
        .filter(Booking.cancellationReason == BookingCancellationReasons.EXPIRED)
        .order_by(Booking.userId)
        .all()
    )


def find_expired_bookings_ordered_by_offerer(expired_on: date = None) -> Query:
    expired_on = expired_on or date.today()
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .join(Venue)
        .join(Offerer)
        .filter(Booking.isCancelled.is_(True))
        .filter(cast(Booking.cancellationDate, Date) == expired_on)
        .filter(Booking.cancellationReason == BookingCancellationReasons.EXPIRED)
        .order_by(Offerer.id)
        .all()
    )


def get_active_bookings_quantity_for_venue(venue_id: int) -> int:
    # Stock.dnBookedQuantity cannot be used here because we exclude used/confirmed bookings.
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .filter(
            venue_id == Offer.venueId,
            Booking.isUsed.is_(False),
            Booking.isCancelled.is_(False),
            Booking.isConfirmed.is_(False),
        )
        .with_entities(coalesce(func.sum(Booking.quantity), 0))
        .one()[0]
    )


def get_validated_bookings_quantity_for_venue(venue_id: int) -> int:
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .filter(Booking.isCancelled.is_(False), venue_id == Offer.venueId)
        .filter(or_(Booking.isUsed.is_(True), Booking.isConfirmed.is_(True)))
        .with_entities(coalesce(func.sum(Booking.quantity), 0))
        .one()[0]
    )


def find_offers_booked_by_beneficiaries(users: list[User]) -> list[Offer]:
    return (
        Offer.query.distinct(Offer.id)
        .join(Stock)
        .join(Booking)
        .filter(Booking.userId.in_(user.id for user in users))
        .all()
    )


def find_cancellable_bookings_by_beneficiaries(users: list[User]) -> list[Booking]:
    return (
        Booking.query.filter(Booking.userId.in_(user.id for user in users))
        .filter(Booking.isCancelled.is_(False))
        .filter(Booking.isUsed.is_(False))
        .all()
    )


def find_cancellable_bookings_by_offerer(offerer_id: int) -> list[Booking]:
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .join(Venue)
        .filter(Venue.managingOffererId == offerer_id)
        .filter(Booking.isCancelled.is_(False))
        .filter(Booking.isUsed.is_(False))
        .all()
    )


def _query_keep_on_non_activation_offers() -> Query:
    offer_types = ["ThingType.ACTIVATION", "EventType.ACTIVATION"]

    return Booking.query.join(Stock).join(Offer).filter(~Offer.type.in_(offer_types))


def _duplicate_booking_when_quantity_is_two(bookings_recap_query: Query) -> Query:
    return bookings_recap_query.union_all(bookings_recap_query.filter(Booking.quantity == 2))


def _build_bookings_recap_query(user_id: int, event_date: Optional[date], venue_id: Optional[int]) -> Query:
    query = (
        Booking.query.outerjoin(Payment)
        .reset_joinpoint()
        .join(User)
        .join(Stock)
        .join(Offer)
        .join(Venue)
        .join(Offerer)
        .join(UserOfferer)
        .filter(UserOfferer.userId == user_id)
        .filter(UserOfferer.validationToken.is_(None))
    )

    if venue_id:
        query = query.filter(Venue.id == venue_id)

    if event_date:
        query = query.filter(
            cast(
                func.timezone(
                    Venue.timezone,
                    func.timezone("UTC", Stock.beginningDatetime),
                ),
                Date,
            )
            == event_date
        )

    query = query.with_entities(
        Booking.token.label("bookingToken"),
        Booking.dateCreated.label("bookingDate"),
        Booking.isCancelled.label("isCancelled"),
        Booking.isUsed.label("isUsed"),
        Booking.quantity.label("quantity"),
        Booking.amount.label("bookingAmount"),
        Booking.dateUsed.label("dateUsed"),
        Booking.cancellationDate.label("cancellationDate"),
        Booking.confirmationDate.label("confirmationDate"),
        Booking.isConfirmed.label("isConfirmed"),
        Offer.name.label("offerName"),
        Offer.id.label("offerId"),
        Offer.extraData.label("offerExtraData"),
        Payment.currentStatus.label("paymentStatus"),
        Payment.lastProcessedDate.label("paymentDate"),
        User.firstName.label("beneficiaryFirstname"),
        User.lastName.label("beneficiaryLastname"),
        User.email.label("beneficiaryEmail"),
        Stock.beginningDatetime.label("stockBeginningDatetime"),
        Venue.departementCode.label("venueDepartementCode"),
        Offerer.name.label("offererName"),
        Offerer.postalCode.label("offererPostalCode"),
        Venue.id.label("venueId"),
        Venue.name.label("venueName"),
        Venue.publicName.label("venuePublicName"),
        Venue.isVirtual.label("venueIsVirtual"),
    )

    return query


def _paginated_bookings_sql_entities_to_bookings_recap(
    paginated_bookings: list[object], page: int, per_page_limit: int, total_bookings_recap: int
) -> BookingsRecapPaginated:
    return BookingsRecapPaginated(
        bookings_recap=[_serialize_booking_recap(booking) for booking in paginated_bookings],
        page=page,
        pages=int(math.ceil(total_bookings_recap / per_page_limit)),
        total=total_bookings_recap,
    )


def _apply_departement_timezone(naive_datetime: datetime, departement_code: str) -> datetime:
    return (
        naive_datetime.astimezone(tz.gettz(get_department_timezone(departement_code)))
        if naive_datetime is not None
        else None
    )


def _serialize_date_with_timezone(date_without_timezone: datetime, booking: AbstractKeyedTuple) -> datetime:
    if booking.venueDepartementCode:
        return _apply_departement_timezone(
            naive_datetime=date_without_timezone, departement_code=booking.venueDepartementCode
        )
    offerer_department_code = PostalCode(booking.offererPostalCode).get_departement_code()
    return _apply_departement_timezone(naive_datetime=date_without_timezone, departement_code=offerer_department_code)


def _serialize_booking_recap(booking: AbstractKeyedTuple) -> BookingRecap:
    kwargs = {
        "offer_identifier": booking.offerId,
        "offer_name": booking.offerName,
        "offerer_name": booking.offererName,
        "beneficiary_email": booking.beneficiaryEmail,
        "beneficiary_firstname": booking.beneficiaryFirstname,
        "beneficiary_lastname": booking.beneficiaryLastname,
        "booking_amount": booking.bookingAmount,
        "booking_token": booking.bookingToken,
        "booking_date": _serialize_date_with_timezone(booking.bookingDate, booking),
        "booking_is_used": booking.isUsed,
        "booking_is_cancelled": booking.isCancelled,
        "booking_is_confirmed": False,
        "booking_is_reimbursed": booking.paymentStatus == TransactionStatus.SENT,
        "booking_is_duo": booking.quantity == DUO_QUANTITY,
        "venue_identifier": booking.venueId,
        "date_used": _serialize_date_with_timezone(booking.dateUsed, booking),
        "payment_date": _serialize_date_with_timezone(booking.paymentDate, booking),
        "cancellation_date": _serialize_date_with_timezone(booking.cancellationDate, booking=booking),
        "confirmation_date": None,
        "venue_name": booking.venuePublicName if booking.venuePublicName else booking.venueName,
        "venue_is_virtual": booking.venueIsVirtual,
    }

    if booking.stockBeginningDatetime:
        klass = EventBookingRecap
        kwargs.update(
            event_beginning_datetime=_apply_departement_timezone(
                booking.stockBeginningDatetime, booking.venueDepartementCode
            ),
            booking_is_confirmed=booking.isConfirmed,
            confirmation_date=_serialize_date_with_timezone(booking.confirmationDate, booking),
        )

    elif booking.offerExtraData and "isbn" in booking.offerExtraData:
        klass = BookBookingRecap
        kwargs["offer_isbn"] = booking.offerExtraData["isbn"]
    else:
        klass = ThingBookingRecap

    return klass(**kwargs)


def _find_bookings_eligible_for_payment() -> Query:
    return _query_keep_only_used_and_non_cancelled_bookings_on_non_activation_offers().filter(
        ~(cast(Stock.beginningDatetime, Date) >= date.today()) | (Stock.beginningDatetime.is_(None))
    )


def _query_keep_only_used_and_non_cancelled_bookings_on_non_activation_offers() -> Query:
    return (
        _query_keep_on_non_activation_offers()
        .join(Venue)
        .filter(Booking.isCancelled.is_(False))
        .filter(Booking.isUsed.is_(True))
    )
