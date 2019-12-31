from datetime import datetime
from typing import Set, List, Union

from sqlalchemy import and_, func
from sqlalchemy.orm import Query

from domain.keywords import create_get_filter_matching_ts_query_in_any_model
from domain.stocks import STOCK_DELETION_DELAY
from models import Booking, EventType, Offer, Offerer, Payment, Product, Recommendation, Stock, ThingType, User, Venue
from models.api_errors import ResourceNotFoundError
from models.db import db

get_filter_matching_ts_query_for_booking = create_get_filter_matching_ts_query_in_any_model(
    Product,
    Venue
)


def _query_keep_on_non_activation_offers() -> Query:
    offer_types = ['ThingType.ACTIVATION', 'EventType.ACTIVATION']

    return Booking.query \
        .join(Stock) \
        .join(Offer) \
        .filter(~Offer.type.in_(offer_types))


def count() -> int:
    return _query_keep_on_non_activation_offers() \
        .count()


def count_by_departement(departement_code: str) -> int:
    return _query_keep_on_non_activation_offers() \
        .join(User, User.id == Booking.userId) \
        .filter(User.departementCode == departement_code) \
        .count()


def count_non_cancelled() -> int:
    return _query_non_cancelled_non_activation_bookings() \
        .count()


def count_non_cancelled_by_departement(departement_code: str) -> int:
    return _query_non_cancelled_non_activation_bookings() \
        .join(User, Booking.userId == User.id) \
        .filter(User.departementCode == departement_code) \
        .count()


def count_cancelled() -> int:
    return _query_cancelled_bookings_on_non_activation_offers() \
        .count()


def count_cancelled_by_departement(departement_code: str) -> int:
    return _query_cancelled_bookings_on_non_activation_offers() \
        .join(User) \
        .filter(User.departementCode == departement_code) \
        .count()


def _query_cancelled_bookings_on_non_activation_offers() -> Query:
    return _query_keep_on_non_activation_offers() \
        .filter(Booking.isCancelled == True)


def find_active_bookings_by_user_id(user_id: int) -> List[Booking]:
    return Booking.query \
        .filter_by(userId=user_id) \
        .filter_by(isCancelled=False) \
        .all()


def find_offerer_bookings(offerer_id: int, venue_id: int = None, offer_id: int = None,
                          date_from: Union[datetime, str] = None, date_to: Union[datetime, str] = None) -> List[
    Booking]:
    query = _filter_bookings_by_offerer_id(offerer_id)

    if venue_id:
        query = query.filter(Venue.id == venue_id)

    if offer_id:
        query = query.filter(Offer.id == offer_id)

        offer = Offer.query.filter(Offer.id == offer_id).first()

        if offer and offer.isEvent and date_from:
            query = query.filter(Stock.beginningDatetime == date_from)

        if offer and offer.isThing:
            if date_from:
                query = query.filter(Booking.dateCreated >= date_from)
            if date_to:
                query = query.filter(Booking.dateCreated <= date_to)

    return query.all()


def find_digital_bookings_for_offerer(offerer_id: int, offer_id: int = None, date_from: Union[datetime, str] = None,
                                      date_to: Union[datetime, str] = None) -> List[Booking]:
    query = _filter_bookings_by_offerer_id(offerer_id)

    query = query.filter(Venue.isVirtual == True)

    if offer_id:
        query = query.filter(Offer.id == offer_id)

    if date_from:
        query = query.filter(Booking.dateCreated >= date_from)

    if date_to:
        query = query.filter(Booking.dateCreated <= date_to)

    return query.all()


def find_from_recommendation(recommendation: Recommendation, user: User) -> List[Booking]:
    return _query_keep_on_non_activation_offers() \
        .filter(Offer.id == recommendation.offerId) \
        .distinct(Booking.stockId) \
        .filter(Booking.userId == user.id) \
        .order_by(Booking.stockId, Booking.isCancelled, Booking.dateCreated.desc()) \
        .all()


def find_for_stock_and_user(stock: Stock, current_user: User) -> List[Booking]:
    return Booking.query \
        .filter_by(userId=current_user.id) \
        .filter_by(isCancelled=False) \
        .filter_by(stockId=stock.id) \
        .all()


def find_by(token: str, email: str = None, offer_id: int = None) -> Booking:
    query = Booking.query.filter_by(token=token)

    if email:
        query = query.join(User) \
            .filter(func.lower(User.email) == email.strip().lower())

    if offer_id:
        query_offer = Booking.query \
            .join(Stock) \
            .join(Offer) \
            .filter_by(id=offer_id)
        query = query.intersect_all(query_offer)

    booking = query.first()

    if booking is None:
        errors = ResourceNotFoundError()
        errors.add_error(
            'bookingNotFound',
            "Cette contremarque n'a pas été trouvée"
        )
        raise errors

    return booking


def find_by_id(booking_id: int) -> Booking:
    return Booking.query \
        .filter_by(id=booking_id) \
        .first_or_404()


def find_ongoing_bookings_by_stock(stock: Stock) -> List[Booking]:
    return Booking.query \
        .filter_by(stockId=stock.id, isCancelled=False, isUsed=False) \
        .all()


def find_eligible_bookings_for_offerer(offerer_id: int) -> List[Booking]:
    return _query_keep_only_used_or_finished_bookings_on_non_activation_offers() \
        .join(Offerer) \
        .filter(Offerer.id == offerer_id) \
        .reset_joinpoint() \
        .outerjoin(Payment) \
        .order_by(Payment.id, Booking.dateCreated.asc()) \
        .all()


def find_eligible_bookings_for_venue(venue_id: int) -> List[Booking]:
    return _query_keep_only_used_or_finished_bookings_on_non_activation_offers() \
        .filter(Venue.id == venue_id) \
        .reset_joinpoint() \
        .outerjoin(Payment) \
        .order_by(Payment.id, Booking.dateCreated.asc()) \
        .all()


def find_date_used(booking: Booking) -> datetime:
    return booking.dateUsed


def find_user_activation_booking(user: User) -> Booking:
    is_activation_offer = (Offer.type == str(ThingType.ACTIVATION)) | (
            Offer.type == str(EventType.ACTIVATION))

    return Booking.query \
        .join(User) \
        .join(Stock, Booking.stockId == Stock.id) \
        .join(Offer) \
        .filter(is_activation_offer) \
        .filter(User.id == user.id) \
        .first()


def find_existing_tokens() -> Set[str]:
    return set(map(lambda t: t[0], db.session.query(Booking.token).all()))


def _filter_bookings_by_offerer_id(offerer_id: int) -> Query:
    return Booking.query \
        .join(Stock) \
        .join(Offer) \
        .join(Venue) \
        .outerjoin(Product, and_(Offer.productId == Product.id)) \
        .filter(Venue.managingOffererId == offerer_id) \
        .reset_joinpoint()


def _query_non_cancelled_non_activation_bookings() -> Query:
    return _query_keep_on_non_activation_offers() \
        .filter(Booking.isCancelled == False)


def _query_keep_only_used_or_finished_bookings_on_non_activation_offers() -> Query:
    booking_on_event_finished_more_than_two_days_ago = (
            datetime.utcnow() > Stock.endDatetime + STOCK_DELETION_DELAY)

    return _query_keep_on_non_activation_offers() \
        .join(Venue) \
        .filter(Booking.isCancelled == False) \
        .filter((Booking.isUsed == True) | booking_on_event_finished_more_than_two_days_ago)


def find_not_used_and_not_cancelled() -> List[Booking]:
    return Booking.query \
        .filter(Booking.isUsed == False) \
        .filter(Booking.isCancelled == False) \
        .all()


def find_for_my_bookings_page(user_id: int) -> List[Booking]:
    return _query_keep_on_non_activation_offers() \
        .distinct(Booking.stockId) \
        .filter(Booking.userId == user_id) \
        .order_by(Booking.stockId, Booking.isCancelled, Booking.dateCreated.desc()) \
        .all()
