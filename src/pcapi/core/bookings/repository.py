from datetime import date
from datetime import datetime
from datetime import time
import math
from typing import List

from dateutil import tz
from sqlalchemy import Date
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.orm import Query
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlalchemy.util._collections import AbstractKeyedTuple

from pcapi.core.bookings import conf
from pcapi.core.bookings.models import BookingCancellationReasons
from pcapi.domain.booking_recap.booking_recap import BookBookingRecap
from pcapi.domain.booking_recap.booking_recap import BookingRecap
from pcapi.domain.booking_recap.booking_recap import EventBookingRecap
from pcapi.domain.booking_recap.booking_recap import ThingBookingRecap
from pcapi.domain.booking_recap.bookings_recap_paginated import BookingsRecapPaginated
import pcapi.domain.expenses
from pcapi.domain.postal_code.postal_code import PostalCode
from pcapi.models import Booking
from pcapi.models import Offer
from pcapi.models import Stock
from pcapi.models import UserOfferer
from pcapi.models import VenueSQLEntity
from pcapi.models.api_errors import ResourceNotFoundError
from pcapi.models.db import db
from pcapi.models.offer_type import EventType
from pcapi.models.offer_type import ThingType
from pcapi.models.offerer import Offerer
from pcapi.models.payment import Payment
from pcapi.models.payment_status import TransactionStatus
from pcapi.models.recommendation import Recommendation
from pcapi.models.user_sql_entity import UserSQLEntity
from pcapi.utils.date import get_department_timezone
from pcapi.utils.token import random_token


DUO_QUANTITY = 2


def find_from_recommendation(recommendation: Recommendation, user_id: int) -> List[Booking]:
    return _build_find_ordered_user_bookings(user_id=user_id).filter(Offer.id == recommendation.offerId).all()


def find_by(token: str, email: str = None, offer_id: int = None) -> Booking:
    query = Booking.query.filter_by(token=token)

    if email:
        query = query.join(UserSQLEntity).filter(func.lower(UserSQLEntity.email) == email.strip().lower())

    if offer_id:
        query_offer = Booking.query.join(Stock).join(Offer).filter_by(id=offer_id)
        query = query.intersect_all(query_offer)

    booking = query.first()

    if booking is None:
        errors = ResourceNotFoundError()
        errors.add_error("global", "Cette contremarque n'a pas été trouvée")
        raise errors

    return booking


def find_by_pro_user_id(user_id: int, page: int = 1, per_page_limit: int = 1000) -> BookingsRecapPaginated:
    bookings_recap_query = _build_bookings_recap_query(user_id)
    bookings_recap_query_with_duplicates = _duplicate_booking_when_quantity_is_two(bookings_recap_query)

    total_bookings_recap = bookings_recap_query_with_duplicates.count()

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


def find_ongoing_bookings_by_stock(stock_id: int) -> List[Booking]:
    return Booking.query.filter_by(stockId=stock_id, isCancelled=False, isUsed=False).all()


def find_not_cancelled_bookings_by_stock(stock: Stock) -> List[Booking]:
    return Booking.query.filter_by(stockId=stock.id, isCancelled=False).all()


def find_bookings_eligible_for_payment_for_offerer(offerer_id: int) -> List[Booking]:
    return (
        _find_bookings_eligible_for_payment()
        .join(Offerer)
        .filter(Offerer.id == offerer_id)
        .reset_joinpoint()
        .outerjoin(Payment)
        .order_by(Payment.id, Booking.dateCreated.asc())
        .all()
    )


def find_bookings_eligible_for_payment_for_venue(venue_id: int) -> List[Booking]:
    return (
        _find_bookings_eligible_for_payment()
        .filter(VenueSQLEntity.id == venue_id)
        .reset_joinpoint()
        .outerjoin(Payment)
        .order_by(Payment.id, Booking.dateCreated.asc())
        .all()
    )


def find_date_used(booking: Booking) -> datetime:
    return booking.dateUsed


def find_user_activation_booking(user: UserSQLEntity) -> Booking:
    is_activation_offer = (Offer.type == str(ThingType.ACTIVATION)) | (Offer.type == str(EventType.ACTIVATION))

    return (
        Booking.query.join(UserSQLEntity)
        .join(Stock, Booking.stockId == Stock.id)
        .join(Offer)
        .filter(is_activation_offer)
        .filter(UserSQLEntity.id == user.id)
        .first()
    )


def token_exists(token: str) -> bool:
    return db.session.query(Booking.query.filter_by(token=token).exists()).scalar()


def find_not_used_and_not_cancelled() -> List[Booking]:
    return Booking.query.filter(Booking.isUsed.is_(False)).filter(Booking.isCancelled.is_(False)).all()


def find_user_bookings_for_recommendation(user_id: int) -> List[Booking]:
    return _build_find_ordered_user_bookings(user_id).all()


def get_only_offer_ids_from_bookings(user: UserSQLEntity) -> List[int]:
    offers_booked = Offer.query.join(Stock).join(Booking).filter_by(userId=user.id).with_entities(Offer.id).all()
    return [offer.id for offer in offers_booked]


def find_used_by_token(token: str) -> Booking:
    return Booking.query.filter_by(token=token).filter_by(isUsed=True).first()


def count_not_cancelled_bookings_quantity_by_stock_id(stock_id: int) -> int:
    bookings = (
        Booking.query.join(Stock).filter(Booking.isCancelled.is_(False)).filter(Booking.stockId == stock_id).all()
    )

    return sum([booking.quantity for booking in bookings])


def find_expiring_bookings() -> Query:
    booking_types_names_that_can_expire = [str(t) for t in ThingType if t.value.get("canExpire", False)]
    today_at_midnight = datetime.combine(date.today(), time(0, 0))
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .filter(Offer.type.in_(booking_types_names_that_can_expire))
        .filter(Booking.isCancelled.is_(False))
        .filter(Booking.isUsed.is_(False))
        .filter(Booking.dateCreated <= today_at_midnight - conf.BOOKINGS_AUTO_EXPIRY_DELAY)
    )


def find_soon_to_be_expiring_booking_ordered_by_user(given_date: date = None) -> Query:
    given_date = given_date or date.today()
    given_date = (
        datetime.combine(given_date, time(0, 0))
        + conf.BOOKINGS_EXPIRY_NOTIFICATION_DELAY
        - conf.BOOKINGS_AUTO_EXPIRY_DELAY
    )
    creation_date_to_check_start = datetime.combine(given_date, time(0, 0))
    creation_date_to_check_end = datetime.combine(given_date, time(23, 59, 59))
    booking_types_names_that_can_expire = [str(t) for t in ThingType if t.value.get("canExpire", False)]

    return (
        Booking.query.join(Stock)
        .join(Offer)
        .filter(Offer.type.in_(booking_types_names_that_can_expire))
        .filter(Booking.isCancelled.is_(False))
        .filter(Booking.isUsed.is_(False))
        .filter(Booking.dateCreated.between(creation_date_to_check_start, creation_date_to_check_end))
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
        .join(VenueSQLEntity)
        .join(Offerer)
        .filter(Booking.isCancelled.is_(True))
        .filter(cast(Booking.cancellationDate, Date) == expired_on)
        .filter(Booking.cancellationReason == BookingCancellationReasons.EXPIRED)
        .order_by(Offerer.id)
        .all()
    )


def _query_keep_on_non_activation_offers() -> Query:
    offer_types = ["ThingType.ACTIVATION", "EventType.ACTIVATION"]

    return Booking.query.join(Stock).join(Offer).filter(~Offer.type.in_(offer_types))


def _duplicate_booking_when_quantity_is_two(bookings_recap_query: Query) -> Query:
    return bookings_recap_query.union_all(bookings_recap_query.filter(Booking.quantity == 2))


def _build_bookings_recap_query(user_id: int) -> Query:
    return (
        Booking.query.outerjoin(Payment)
        .reset_joinpoint()
        .join(UserSQLEntity)
        .join(Stock)
        .join(Offer)
        .join(VenueSQLEntity)
        .join(Offerer)
        .join(UserOfferer)
        .filter(UserOfferer.userId == user_id)
        .filter(UserOfferer.validationToken.is_(None))
        .with_entities(
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
            UserSQLEntity.firstName.label("beneficiaryFirstname"),
            UserSQLEntity.lastName.label("beneficiaryLastname"),
            UserSQLEntity.email.label("beneficiaryEmail"),
            Stock.beginningDatetime.label("stockBeginningDatetime"),
            VenueSQLEntity.departementCode.label("venueDepartementCode"),
            Offerer.name.label("offererName"),
            Offerer.postalCode.label("offererPostalCode"),
            VenueSQLEntity.id.label("venueId"),
            VenueSQLEntity.name.label("venueName"),
            VenueSQLEntity.publicName.label("venuePublicName"),
            VenueSQLEntity.isVirtual.label("venueIsVirtual"),
        )
    )


def _paginated_bookings_sql_entities_to_bookings_recap(
    paginated_bookings: List[object], page: int, per_page_limit: int, total_bookings_recap: int
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
    if booking.stockBeginningDatetime:
        return _serialize_event_booking_recap(booking)

    if booking.offerExtraData and "isbn" in booking.offerExtraData:
        return _serialize_book_booking_recap(booking)

    return _serialize_thing_booking_recap(booking)


def _serialize_thing_booking_recap(booking: AbstractKeyedTuple) -> ThingBookingRecap:
    return ThingBookingRecap(
        offer_identifier=booking.offerId,
        offer_name=booking.offerName,
        offerer_name=booking.offererName,
        beneficiary_email=booking.beneficiaryEmail,
        beneficiary_firstname=booking.beneficiaryFirstname,
        beneficiary_lastname=booking.beneficiaryLastname,
        booking_amount=booking.bookingAmount,
        booking_token=booking.bookingToken,
        booking_date=_serialize_date_with_timezone(date_without_timezone=booking.bookingDate, booking=booking),
        booking_is_used=booking.isUsed,
        booking_is_cancelled=booking.isCancelled,
        booking_is_confirmed=False,
        booking_is_reimbursed=booking.paymentStatus == TransactionStatus.SENT,
        booking_is_duo=booking.quantity == DUO_QUANTITY,
        venue_identifier=booking.venueId,
        date_used=_serialize_date_with_timezone(date_without_timezone=booking.dateUsed, booking=booking),
        payment_date=_serialize_date_with_timezone(date_without_timezone=booking.paymentDate, booking=booking),
        cancellation_date=_serialize_date_with_timezone(
            date_without_timezone=booking.cancellationDate, booking=booking
        ),
        confirmation_date=None,
        venue_name=booking.venuePublicName if booking.venuePublicName else booking.venueName,
        venue_is_virtual=booking.venueIsVirtual,
    )


def _serialize_book_booking_recap(booking: AbstractKeyedTuple) -> BookBookingRecap:
    return BookBookingRecap(
        offer_identifier=booking.offerId,
        offer_name=booking.offerName,
        offerer_name=booking.offererName,
        offer_isbn=booking.offerExtraData["isbn"],
        beneficiary_email=booking.beneficiaryEmail,
        beneficiary_firstname=booking.beneficiaryFirstname,
        beneficiary_lastname=booking.beneficiaryLastname,
        booking_amount=booking.bookingAmount,
        booking_token=booking.bookingToken,
        booking_date=_serialize_date_with_timezone(date_without_timezone=booking.bookingDate, booking=booking),
        booking_is_used=booking.isUsed,
        booking_is_cancelled=booking.isCancelled,
        booking_is_confirmed=False,
        booking_is_reimbursed=booking.paymentStatus == TransactionStatus.SENT,
        booking_is_duo=booking.quantity == DUO_QUANTITY,
        venue_identifier=booking.venueId,
        date_used=_serialize_date_with_timezone(date_without_timezone=booking.dateUsed, booking=booking),
        payment_date=_serialize_date_with_timezone(date_without_timezone=booking.paymentDate, booking=booking),
        cancellation_date=_serialize_date_with_timezone(
            date_without_timezone=booking.cancellationDate, booking=booking
        ),
        confirmation_date=None,
        venue_name=booking.venuePublicName if booking.venuePublicName else booking.venueName,
        venue_is_virtual=booking.venueIsVirtual,
    )


def _serialize_event_booking_recap(booking: AbstractKeyedTuple) -> EventBookingRecap:
    return EventBookingRecap(
        offer_identifier=booking.offerId,
        offer_name=booking.offerName,
        offerer_name=booking.offererName,
        beneficiary_email=booking.beneficiaryEmail,
        beneficiary_firstname=booking.beneficiaryFirstname,
        beneficiary_lastname=booking.beneficiaryLastname,
        booking_amount=booking.bookingAmount,
        booking_token=booking.bookingToken,
        booking_date=_serialize_date_with_timezone(date_without_timezone=booking.bookingDate, booking=booking),
        booking_is_used=booking.isUsed,
        booking_is_cancelled=booking.isCancelled,
        booking_is_confirmed=booking.isConfirmed,
        booking_is_reimbursed=booking.paymentStatus == TransactionStatus.SENT,
        booking_is_duo=booking.quantity == DUO_QUANTITY,
        event_beginning_datetime=_apply_departement_timezone(
            naive_datetime=booking.stockBeginningDatetime, departement_code=booking.venueDepartementCode
        ),
        date_used=_serialize_date_with_timezone(date_without_timezone=booking.dateUsed, booking=booking),
        confirmation_date=_serialize_date_with_timezone(
            date_without_timezone=booking.confirmationDate, booking=booking
        ),
        payment_date=_serialize_date_with_timezone(date_without_timezone=booking.paymentDate, booking=booking),
        cancellation_date=_serialize_date_with_timezone(
            date_without_timezone=booking.cancellationDate, booking=booking
        ),
        venue_identifier=booking.venueId,
        venue_name=booking.venuePublicName if booking.venuePublicName else booking.venueName,
        venue_is_virtual=booking.venueIsVirtual,
    )


def _find_bookings_eligible_for_payment() -> Query:
    return _query_keep_only_used_and_non_cancelled_bookings_on_non_activation_offers().filter(
        ~(cast(Stock.beginningDatetime, Date) >= date.today()) | (Stock.beginningDatetime.is_(None))
    )


def _query_keep_only_used_and_non_cancelled_bookings_on_non_activation_offers() -> Query:
    return (
        _query_keep_on_non_activation_offers()
        .join(VenueSQLEntity)
        .filter(Booking.isCancelled.is_(False))
        .filter(Booking.isUsed.is_(True))
    )


def _build_find_ordered_user_bookings(user_id: int) -> Query:
    return (
        Booking.query.join(Stock)
        .join(Offer)
        .distinct(Booking.stockId)
        .filter(Booking.userId == user_id)
        .order_by(Booking.stockId, Booking.isCancelled, Booking.dateCreated.desc())
        .options(selectinload(Booking.stock))
    )


def get_user_expenses(user: UserSQLEntity) -> dict:
    bookings = (
        Booking.query.filter_by(user=user)
        .filter_by(isCancelled=False)
        .options(joinedload(Booking.stock).joinedload(Stock.offer))
        .all()
    )
    return pcapi.domain.expenses.get_expenses(bookings)
