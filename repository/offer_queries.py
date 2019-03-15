from datetime import datetime
from typing import List

from sqlalchemy import func, and_, or_

from domain.departments import ILE_DE_FRANCE_DEPT_CODES
from domain.keywords import create_filter_matching_all_keywords_in_any_model, \
    create_get_filter_matching_ts_query_in_any_model, \
    get_first_matching_keywords_string_at_column
from models import Booking, \
    Event, \
    EventType, \
    Offer, \
    Stock, \
    Offerer, \
    Recommendation, \
    Thing, \
    ThingType, \
    Venue
from repository.user_offerer_queries import filter_query_where_user_is_user_offerer_and_is_validated
from utils.distance import get_sql_geo_distance_in_kilometers
from utils.logger import logger


def build_offer_search_base_query():
    return Offer.query.outerjoin(Event) \
        .outerjoin(Thing) \
        .join(Venue) \
        .join(Offerer)


def department_or_national_offers(query, offer_type, departement_codes):
    if '00' in departement_codes:
        return query
    query = query.filter(
        Venue.departementCode.in_(departement_codes) | (offer_type.isNational == True)
    )
    logger.debug(lambda: '(reco) departement .count ' + str(query.count()))
    return query


def bookable_offers(query, offer_type):
    # remove events for which all occurrences are in the past
    # (crude filter to limit joins before the more complete one below)
    if offer_type == Event:
        query = query.filter(Offer.stocks.any(Stock.beginningDatetime > datetime.utcnow()))
        logger.debug(lambda: '(reco) future events.count ' + str(query.count()))

    query = _filter_bookable_offers_for_discovery(query)
    logger.debug(lambda: '(reco) bookable .count ' + str(query.count()))
    return query


def with_active_and_validated_offerer(query):
    query = query.filter((Offerer.isActive == True)
                         & (Offerer.validationToken == None))
    logger.debug(lambda: '(reco) from active and validated offerer .count' + str(query.count()))
    return query


def not_activation_offers(query, offer_type):
    if offer_type == Event:
        return query.filter(Event.type != str(EventType.ACTIVATION))
    else:
        return query.filter(Thing.type != str(ThingType.ACTIVATION))


def not_currently_recommended_offers(query, user):
    valid_recommendation_for_user = (Recommendation.userId == user.id) \
                                    & (Recommendation.search == None) \
                                    & (Recommendation.validUntilDate > datetime.utcnow())

    query = query.filter(~(Offer.recommendations.any(valid_recommendation_for_user)))

    logger.debug(lambda: '(reco) not already used offers.count ' + str(query.count()))
    return query


def get_active_offers_by_type(offer_type, user=None, departement_codes=None, offer_id=None):
    query = Offer.query.filter_by(isActive=True)
    logger.debug(lambda: '(reco) {} active offers count {}'.format(offer_type.__name__, query.count()))
    query = query.join(Stock, and_(Offer.id == Stock.offerId))
    logger.debug(lambda: '(reco) {} offers with stock count {}'.format(offer_type.__name__, query.count()))

    query = query.join(Venue, and_(Offer.venueId == Venue.id))
    query = query.filter(Venue.validationToken == None)
    query = query.join(Offerer)
    if offer_type == Event:
        query = query.join(Event, and_(Offer.eventId == Event.id))
    else:
        query = query.join(Thing, and_(Offer.thingId == Thing.id))
    logger.debug(lambda: '(reco) {} offers with venue offerer {}'.format(offer_type.__name__, query.count()))

    if offer_id is not None:
        query = query.filter(Offer.id == offer_id)
    logger.debug(lambda: '(reco) all ' + str(offer_type) + '.count ' + str(query.count()))

    query = department_or_national_offers(query, offer_type, departement_codes)
    logger.debug(lambda:
                 '(reco) department or national {} {} in {}'.format(offer_type.__name__, str(departement_codes),
                                                                     query.count()))
    query = bookable_offers(query, offer_type)
    logger.debug(lambda: '(reco) bookable_offers {} {}'.format(offer_type.__name__, query.count()))
    query = with_active_and_validated_offerer(query)
    logger.debug(lambda: '(reco) active and validated {} {}'.format(offer_type.__name__, query.count()))
    query = not_currently_recommended_offers(query, user)
    query = not_activation_offers(query, offer_type)
    query = query.distinct(offer_type.id)
    logger.debug(lambda: '(reco) distinct {} {}'.format(offer_type.__name__, query.count()))
    return query.all()


def _date_interval_to_filter(date_interval):
    return ((Stock.beginningDatetime >= date_interval[0]) & \
            (Stock.beginningDatetime <= date_interval[1]))


def filter_offers_with_keywords_string(query, keywords_string):
    get_filter_matching_ts_query_for_offer = create_get_filter_matching_ts_query_in_any_model(
        Event,
        Thing,
        Venue,
        Offerer
    )

    keywords_filter = create_filter_matching_all_keywords_in_any_model(
        get_filter_matching_ts_query_for_offer,
        keywords_string
    )

    query = query.filter(keywords_filter)

    return query


def get_is_offer_selected_by_keywords_string_at_column(offer, keywords_string, column):
    query = build_offer_search_base_query().filter_by(id=offer.id)

    return get_first_matching_keywords_string_at_column(
        query,
        keywords_string,
        column
    ) is not None


def get_offers_for_recommendations_search(
        date=None,
        page=1,
        page_size=10,
        keywords_string=None,
        type_values=None,
        latitude=None,
        longitude=None,
        max_distance=None,
        days_intervals=None):
    # NOTE: filter_out_offers_on_soft_deleted_stocks filter then
    # the offer with event that has NO event occurrence
    # Do we exactly want this ?

    query = _filter_recommendable_offers_for_search(build_offer_search_base_query())

    if max_distance is not None and latitude is not None and longitude is not None:
        distance_instrument = get_sql_geo_distance_in_kilometers(
            Venue.latitude,
            Venue.longitude,
            latitude,
            longitude
        )

        query = query.filter(distance_instrument < max_distance) \
            .reset_joinpoint()

    if days_intervals is not None:
        event_beginningdate_in_interval_filter = or_(*map(
            _date_interval_to_filter, days_intervals))
        query = query.filter(
            event_beginningdate_in_interval_filter | \
            (Offer.thing != None)) \
            .reset_joinpoint()

    if keywords_string is not None:
        query = filter_offers_with_keywords_string(query, keywords_string)

    if type_values is not None:
        event_query = query.filter(Event.type.in_(type_values))

        thing_query = query.filter(Thing.type.in_(type_values))

        query = event_query.union_all(thing_query)

    if page is not None:
        query = query \
            .offset((page - 1) * page_size) \
            .limit(page_size)

    return query.all()


def find_offers_with_filter_parameters(
        user,
        offerer_id=None,
        venue_id=None,
        keywords_string=None
):
    query = build_offer_search_base_query()

    if venue_id is not None:
        query = query.filter(Offer.venueId == venue_id)

    if keywords_string is not None:
        query = filter_offers_with_keywords_string(
            query,
            keywords_string
        )

    if offerer_id is not None:
        query = query.filter(Venue.managingOffererId == offerer_id)

    if not user.isAdmin:
        query = filter_query_where_user_is_user_offerer_and_is_validated(
            query,
            user
        )

    return query

def _has_remaining_stock_predicate():
    return (Stock.available == None) \
           | (Stock.available > Booking.query.filter((Booking.stockId == Stock.id) & (Booking.isCancelled == False))
                                             .statement.with_only_columns([func.coalesce(func.sum(Booking.quantity), 0)]))

def find_searchable_offer(offer_id):
    return Offer.query.filter_by(id=offer_id) \
        .join(Venue) \
        .filter(Venue.validationToken == None) \
        .first()

def _filter_recommendable_offers_for_search(offer_query):
    stock_can_still_be_booked = (Stock.bookingLimitDatetime > datetime.utcnow()) | (Stock.bookingLimitDatetime == None)
    event_has_not_began_yet = (Stock.beginningDatetime != None) & (Stock.beginningDatetime > datetime.utcnow())
    offer_is_on_a_thing = Offer.eventId == None

    offer_query = offer_query.reset_joinpoint() \
        .filter(Offer.isActive == True) \
        .join(Stock) \
        .filter(Stock.isSoftDeleted == False) \
        .filter(stock_can_still_be_booked) \
        .filter(event_has_not_began_yet | offer_is_on_a_thing) \
        .filter((Offerer.validationToken == None) & (Offerer.isActive == True)) \
        .filter(_has_remaining_stock_predicate())

    return offer_query


def find_activation_offers(departement_code: str) -> List[Offer]:
    departement_codes = ILE_DE_FRANCE_DEPT_CODES if departement_code == '93' else [departement_code]
    match_department_or_is_national = or_(Venue.departementCode.in_(departement_codes), Event.isNational == True,
                                          Thing.isNational == True)
    join_on_event = and_(Event.id == Offer.eventId)

    query = Offer.query \
        .outerjoin(Thing) \
        .outerjoin(Event, join_on_event) \
        .join(Venue) \
        .reset_joinpoint() \
        .join(Stock) \
        .filter(Event.type == str(EventType.ACTIVATION)) \
        .filter(match_department_or_is_national)

    query = _filter_bookable_offers_for_discovery(query)

    return query


def _filter_bookable_offers_for_discovery(query):
    return query.filter((Stock.isSoftDeleted == False)
                        & ((Stock.bookingLimitDatetime == None)
                           | (Stock.bookingLimitDatetime > datetime.utcnow()))
                        & _has_remaining_stock_predicate())


def count_offers_for_things_only_by_venue_id(venue_id):
    offer_count = Offer.query \
        .filter_by(venueId=venue_id) \
        .filter(Offer.thing is not None) \
        .count()
    return offer_count


def find_offer_for_venue_id_and_specific_thing(venue_id, thing):
    offer = Offer.query \
        .filter_by(venueId=venue_id) \
        .filter_by(thing=thing) \
        .one_or_none()
    return offer


def find_offer_by_id(offer_id):
    return Offer.query.get(offer_id)


def find_first_offer_linked_to_event(event):
    return Offer.query.join(Event).filter_by(id=event.id).first()


def find_first_offer_linked_to_thing(thing):
    return Offer.query.join(Thing).filter_by(id=thing.id).first()
