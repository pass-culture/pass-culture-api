""" booking queries """
from flask import render_template
from sqlalchemy.exc import InternalError
from sqlalchemy.orm import aliased

from domain.reimbursement import get_all_reimbursements_by_id
from models import ApiErrors, \
    Booking, \
    Event, \
    EventOccurrence, \
    PcObject, \
    Offer, \
    Stock, \
    Thing, \
    User, \
    Venue
from models.db import db
from utils.human_ids import dehumanize
from utils.includes import PRO_BOOKING_INCLUDES
from utils.rest import handle_rest_get_list
from utils.search import get_keywords_filter
from validation.errors import ResourceNotFound


def find_all_by_user_id(user_id):
    return Booking.query.filter_by(userId=user_id).all()


def find_all_by_stock_id(stock):
    return Booking.query.filter_by(stockId=stock.id).all()


def create_resolve_booking_reimbursements(reimbursements_by_id, include=None):
    def resolve(booking, filters):
        booking_reimbursement = reimbursements_by_id[dehumanize(booking['id'])]
        return booking_reimbursement.as_dict(include=include)
    return resolve

def get_bookings_metadata(bookings):
    metadata = {

    }
    return metadata

def find_offerer_bookings(offerer_id, search=None, order_by=None, page=1):

    # ROOT QUERY
    query = Booking.query.join(Stock) \
        .outerjoin(EventOccurrence) \
        .join(Offer,
              ((Stock.offerId == Offer.id) | \
               (EventOccurrence.offerId == Offer.id))) \
        .join(Venue) \
        .filter(Venue.managingOffererId == offerer_id)

    # WE NEED TO HAVE ALL THE BOOKINGS PER OFFERER
    # TO COMPUTE THE REIMBURSEMENT RULES
    # (AND WE LATER BIND THESE VALUES AT RESOLVE AS DICT TIME)
    reimbursements_by_id = get_all_reimbursements_by_id(query.all())

    # FILTER WITH SPECIFIC QUERIES ASKED BY THE CLIENT
    if search:
        query = query.outerjoin(Event)\
                     .outerjoin(Thing)\
                     .filter(get_keywords_filter([Event, Thing, Venue], search))

    # RETURN WITH A RESOLVE FUNCTION
    # TO BIND THE REIMBURSEMENT PROPS
    return handle_rest_get_list(Booking,
                                include=PRO_BOOKING_INCLUDES,
                                order_by=order_by,
                                page=page,
                                paginate=10,
                                query=query,
                                resolve=create_resolve_booking_reimbursements(
                                    reimbursements_by_id,
                                    include=PRO_BOOKING_INCLUDES
                                ))


def find_bookings_from_recommendation(reco, user):
    booking_query = Booking.query.join(Stock)
    if reco.offer.eventId:
        booking_query = booking_query.join(EventOccurrence)
    booking_query = booking_query.join(Offer) \
        .filter(Booking.user == user) \
        .filter(Offer.id == reco.offerId)
    return booking_query.all()


def find_all_bookings_for_stock(stock):
    return Booking.query.join(Stock).filter_by(id=stock.id).all()


def find_by(token, email=None, offer_id=None):
    query = Booking.query.filter_by(token=token)

    if email:
        query = query.join(User).filter_by(email=email)

    if offer_id:
        query_offer_1 = Booking.query.join(Stock) \
            .join(Offer) \
            .filter_by(id=offer_id)
        query_offer_2 = Booking.query.join(Stock) \
            .join(EventOccurrence) \
            .join(aliased(Offer)) \
            .filter_by(id=offer_id)
        query_offer = query_offer_1.union_all(query_offer_2)
        query = query.intersect_all(query_offer)

    booking = query.first()

    if booking is None:
        errors = ResourceNotFound()
        errors.addError(
            'global',
            "Cette contremarque n'a pas été trouvée"
        )
        raise errors

    return booking


def save_booking(booking):
    try:
        PcObject.check_and_save(booking)
    except InternalError as internal_error:
        api_errors = ApiErrors()

        if 'tooManyBookings' in str(internal_error.orig):
            api_errors.addError('global', 'la quantité disponible pour cette offre est atteinte')
        elif 'insufficientFunds' in str(internal_error.orig):
            api_errors.addError('insufficientFunds', 'l\'utilisateur ne dispose pas de fonds suffisants pour '
                                                     'effectuer une réservation.')
        raise api_errors


def find_bookings_stats_per_department(time_intervall):
    query = render_template('exports/find_bookings_stats_per_departement.sql', time_intervall=time_intervall)
    return db.engine.execute(query).fetchall()


def find_bookings_in_date_range_for_given_user_or_venue_departement(booking_date_max, booking_date_min, event_date_max,
                                                                    event_date_min, user_department, venue_department):
    query = render_template('exports/find_bookings_in_date_range_for_given_user_or_venue_departement.sql',
                            booking_date_max=booking_date_max, booking_date_min=booking_date_min,
                            event_date_max=event_date_max, event_date_min=event_date_min,
                            user_department=user_department, venue_department=venue_department)
    return db.engine.execute(query).fetchall()


def find_by_id(booking_id):
    return Booking.query.filter_by(id=booking_id).first_or_404()


def find_all_ongoing_bookings_by_stock(stock):
    return Booking.query.filter_by(stockId=stock.id, isCancelled=False, isUsed=False).all()


def find_all_bookings_for_event_occurrence(event_occurrence):
    return Booking.query.join(Stock).join(EventOccurrence).filter_by(id=event_occurrence.id).all()
