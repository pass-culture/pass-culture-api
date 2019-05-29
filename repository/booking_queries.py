from datetime import datetime
from typing import Set

from postgresql_audit.flask import versioning_manager
from sqlalchemy import and_, text, func

from domain.keywords import create_filter_matching_all_keywords_in_any_model, \
    create_get_filter_matching_ts_query_in_any_model
from domain.stocks import STOCK_DELETION_DELAY
from models import Booking, \
    Offer, \
    Stock, \
    User, \
    Product, \
    Venue, Offerer, ThingType, Payment
from models.api_errors import ResourceNotFound
from models.db import db
from utils.rest import query_with_order_by, check_order_by

get_filter_matching_ts_query_for_booking = create_get_filter_matching_ts_query_in_any_model(
    Product,
    Venue
)


def find_active_bookings_by_user_id(user_id):
    return Booking.query \
        .filter_by(userId=user_id) \
        .filter_by(isCancelled=False) \
        .all()


def find_all_by_stock_id(stock):
    return Booking.query.filter_by(stockId=stock.id).all()


def filter_bookings_with_keywords_string(query, keywords_string):
    keywords_filter = create_filter_matching_all_keywords_in_any_model(
        get_filter_matching_ts_query_for_booking,
        keywords_string
    )
    query = query \
        .outerjoin(Product) \
        .outerjoin(Venue) \
        .filter(keywords_filter) \
        .reset_joinpoint()
    return query


def filter_bookings_by_offerer_id(offerer_id):
    query = Booking.query.join(Stock) \
        .join(Offer) \
        .join(Venue) \
        .outerjoin(Product, and_(Offer.productId == Product.id)) \
        .filter(Venue.managingOffererId == offerer_id) \
        .reset_joinpoint()
    return query


def find_offerer_bookings_paginated(offerer_id, search=None, order_by=None, page=1):
    query = filter_bookings_by_offerer_id(offerer_id)

    if search:
        query = filter_bookings_with_keywords_string(query, search)

    if order_by:
        check_order_by(order_by)
        query = query_with_order_by(query, order_by)

    bookings = query.paginate(int(page), per_page=10, error_out=False) \
        .items

    return bookings


def find_all_offerer_bookings(offerer_id):
    query = filter_bookings_by_offerer_id(offerer_id)

    bookings = query.all()

    return bookings


def find_bookings_from_recommendation(reco, user):
    booking_query = Booking.query \
        .join(Stock) \
        .join(Offer) \
        .filter(Booking.user == user) \
        .filter(Offer.id == reco.offerId)
    return booking_query.all()


def find_all_bookings_for_stock(stock):
    return Booking.query.join(Stock).filter_by(id=stock.id).all()


def find_all_bookings_for_stock_and_user(stock, current_user):
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
        query = Booking.query \
            .join(Stock) \
            .join(Offer) \
            .filter_by(id=offer_id)

    booking = query.first()

    if booking is None:
        errors = ResourceNotFound()
        errors.addError(
            'global',
            "Cette contremarque n'a pas été trouvée"
        )
        raise errors

    return booking


def find_by_id(booking_id):
    return Booking.query.filter_by(id=booking_id).first_or_404()


def find_all_ongoing_bookings_by_stock(stock):
    return Booking.query.filter_by(stockId=stock.id, isCancelled=False, isUsed=False).all()


def find_final_offerer_bookings(offerer_id):
    booking_on_event_finished_more_than_two_days_ago = (datetime.utcnow() > Stock.endDatetime + STOCK_DELETION_DELAY)

    return Booking.query \
        .join(Stock) \
        .join(Offer) \
        .join(Venue) \
        .join(Offerer) \
        .filter(Offerer.id == offerer_id) \
        .filter(Booking.isCancelled == False) \
        .filter((Booking.isUsed == True) | booking_on_event_finished_more_than_two_days_ago) \
        .reset_joinpoint() \
        .outerjoin(Payment) \
        .order_by(Payment.id, Booking.dateCreated.asc()) \
        .all()


def find_date_used(booking: Booking) -> datetime:
    Activity = versioning_manager.activity_cls
    find_by_id_and_is_used = "table_name='booking' " \
                             "AND verb='update' " \
                             "AND cast(old_data->>'id' AS INT) = %s " \
                             "AND cast(changed_data->>'isUsed' as boolean) = true" % booking.id

    activity = Activity.query.filter(text(find_by_id_and_is_used)).first()
    return activity.issued_at if activity else None


def find_user_activation_booking(user: User) -> User:
    return Booking.query \
        .join(User) \
        .join(Stock, Booking.stockId == Stock.id) \
        .join(Offer) \
        .join(Product) \
        .filter(Product.type == str(ThingType.ACTIVATION)) \
        .filter(User.id == user.id) \
        .first()


def get_existing_tokens() -> Set[str]:
    return set(map(lambda t: t[0], db.session.query(Booking.token).all()))
