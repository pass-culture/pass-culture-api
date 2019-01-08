from sqlalchemy import or_
from datetime import datetime

from domain.keywords import create_filter_finding_all_keywords_in_at_least_one_of_the_models,\
                            create_ts_filter_finding_ts_query_in_at_least_one_of_the_models
from models import Offerer, Venue, Offer, EventOccurrence, UserOfferer, User, Event, Booking, Stock, Recommendation
from models import RightsType
from models.activity import load_activity
from models.db import db

offerer_ts_filter = create_ts_filter_finding_ts_query_in_at_least_one_of_the_models(
    Offerer
)

def get_by_offer_id(offer_id):
    return Offerer.query.join(Venue).join(Offer).filter_by(id=offer_id).first()


def get_by_event_occurrence_id(event_occurrence_id):
    return Offerer.query.join(Venue).join(Offer).join(EventOccurrence).filter_by(id=event_occurrence_id).first()


def find_all_admin_offerer_emails(offerer_id):
    return [result.email for result in Offerer.query.filter_by(id=offerer_id).join(UserOfferer).filter_by(rights=RightsType.admin).filter_by(validationToken=None).join(
        User).with_entities(User.email)]


def find_all_recommendations_for_offerer(offerer):
    return Recommendation.query.join(Offer).join(Venue).join(Offerer).filter_by(id=offerer.id).all()


def find_all_offerers_with_managing_user_information():
    query = db.session.query(Offerer.id, Offerer.name, Offerer.siren, Offerer.postalCode, Offerer.city, User.firstName,
                             User.lastName, User.email, User.phoneNumber, User.postalCode) \
        .join(UserOfferer) \
        .join(User)

    result = query.order_by(Offerer.name, User.email).all()
    return result


def find_all_offerers_with_managing_user_information_and_venue():
    query = db.session.query(Offerer.id, Offerer.name, Offerer.siren, Offerer.postalCode, Offerer.city, Venue.name,
                             Venue.bookingEmail, Venue.postalCode, User.firstName, User.lastName, User.email,
                             User.phoneNumber, User.postalCode) \
        .join(UserOfferer) \
        .join(User) \
        .join(Venue)

    result = query.order_by(Offerer.name, Venue.name, User.email).all()
    return result


def find_all_offerers_with_managing_user_information_and_not_virtual_venue():
    query = db.session.query(Offerer.id, Offerer.name, Offerer.siren, Offerer.postalCode, Offerer.city, Venue.name,
                             Venue.bookingEmail, Venue.postalCode, User.firstName, User.lastName, User.email,
                             User.phoneNumber, User.postalCode) \
        .join(UserOfferer) \
        .join(User) \
        .join(Venue)

    result = query.filter(Venue.isVirtual == False).order_by(Offerer.name, Venue.name, User.email).all()
    return result


def find_all_offerers_with_venue():
    query = db.session.query(Offerer.id, Offerer.name, Venue.id, Venue.name, Venue.bookingEmail, Venue.postalCode,
                             Venue.isVirtual) \
        .join(Venue)

    result = query.order_by(Offerer.name, Venue.name, Venue.id).all()
    return result


def find_all_pending_validation():
    return Offerer.query.join(UserOfferer) \
        .filter(or_(UserOfferer.validationToken != None, Offerer.validationToken != None)) \
        .order_by(Offerer.id).all()


def find_first_by_user_offerer_id(user_offerer_id):
    return Offerer.query.join(UserOfferer).filter_by(id=user_offerer_id).first()


def find_filtered_offerers(sirens=None,
                           dpts=None,
                           zip_codes=None,
                           from_date=None,
                           to_date=None,
                           has_siren=None,
                           has_bank_information=None,
                           is_validated=None,
                           is_active=None,
                           has_not_virtual_venue=None,
                           has_validated_venue=None,
                           has_venue_with_siret=None,
                           offer_status=None,
                           has_validated_user=None,
                           has_validated_user_offerer=None):

    query = db.session.query(Offerer)
    if sirens is not None:
        query = _filter_by_sirens(query, sirens)

    if dpts is not None:
        query = _filter_by_dpts(query, dpts)

    if zip_codes is not None:
        query = _filter_by_zip_codes(query, zip_codes)

    if from_date is not None or to_date is not None:
        query = _filter_by_date(query, from_date, to_date)

    if has_siren is not None:
        query = _filter_by_has_siren(query, has_siren)

    if has_bank_information is not None:
        query = _filter_by_has_bank_information(query, has_bank_information)

    if is_validated is not None:
        query = _filter_by_is_validated(query, is_validated)

    if is_active is not None:
        query = _filter_by_is_active(query, is_active)

    if has_not_virtual_venue is not None or has_validated_venue is not None \
     or offer_status is not None or has_venue_with_siret is not None:
        query = query.join(Venue)

    if has_not_virtual_venue is not None:
        query = _filter_by_has_not_virtual_venue(query, has_not_virtual_venue)

    if has_validated_venue is not None:
        query = _filter_by_has_validated_venue(query, has_validated_venue)

    if has_venue_with_siret is not None:
        query = _filter_by_has_venue_with_siret(query, has_venue_with_siret)

    if offer_status is not None:
        query = _filter_by_offer_status(query, offer_status)

    if has_validated_user_offerer is not None or has_validated_user is not None:
        query = query.join(UserOfferer)

    if has_validated_user_offerer is not None:
        query = _filter_by_has_validated_user_offerer(query, has_validated_user_offerer)

    if has_validated_user is not None:
        query = query.join(User)
        query = _filter_by_has_validated_user(query, has_validated_user)


    result = query.all()
    return result


def _filter_by_sirens(query, sirens):
    return query.filter(Offerer.siren.in_(sirens))


def _filter_by_dpts(query, dpts):
    dpts_filter = _create_filter_from_dpts_list(dpts)

    query = query.filter(dpts_filter)
    return query


def  _create_filter_from_dpts_list(dpts):
    previous_dpts_filter = None
    dpts_filter = None
    final_dpts_filter = None

    for dpt in dpts:
        if dpts_filter is not None:
            previous_dpts_filter = dpts_filter
            if final_dpts_filter is not None:
                previous_dpts_filter = final_dpts_filter

        dpts_filter = Offerer.postalCode.like(dpt + '%')

        if previous_dpts_filter is not None:
            final_dpts_filter = previous_dpts_filter | dpts_filter

    return final_dpts_filter


def _filter_by_zip_codes(query, zip_codes):
    return query.filter(Offerer.postalCode.in_(zip_codes))


def _filter_by_date(query, from_date, to_date):
    if from_date:
        query = query.filter(Offerer.dateCreated >= from_date)
    if to_date:
        query = query.filter(Offerer.dateCreated <= to_date)
    return query


def _filter_by_has_siren(query, has_siren):
    if has_siren:
        query = query.filter(Offerer.siren != None)
    else:
        query = query.filter(Offerer.siren == None)
    return query


def _filter_by_is_validated(query, is_validated):
    if is_validated:
        query = query.filter(Offerer.validationToken == None)
    else:
        query = query.filter(Offerer.validationToken != None)
    return query


def _filter_by_has_bank_information(query, has_bank_information):
    if has_bank_information:
        query = query.filter(Offerer.bic != None)
    else:
        query = query.filter(Offerer.bic == None)
    return query


def _filter_by_is_active(query, is_active):
    if is_active:
        query = query.filter(Offerer.isActive)
    else:
        query = query.filter(~Offerer.isActive)
    return query


def _filter_by_has_not_virtual_venue(query, has_not_virtual_venue):
    is_not_virtual = Venue.isVirtual == False
    if has_not_virtual_venue:
        query = query.filter(Offerer.managedVenues.any(is_not_virtual))
    else:
        query = query.filter(~Offerer.managedVenues.any(is_not_virtual))
    return query


def _filter_by_has_validated_venue(query, has_validated_venue):
    is_valid = Venue.validationToken == None
    if has_validated_venue:
        query = query.filter(Offerer.managedVenues.any(is_valid))
    else:
        query = query.filter(~Offerer.managedVenues.any(is_valid))
    return query


def _filter_by_has_venue_with_siret(query, has_venue_with_siret):
    has_siret = Venue.siret != None
    if has_venue_with_siret:
        query = query.filter(Offerer.managedVenues.any(has_siret))
    else:
        query = query.filter(~Offerer.managedVenues.any(has_siret))
    return query


def _filter_by_offer_status(query, offer_status):
    if offer_status == 'ALL':
        query = query.join(Offer)
    elif offer_status == "WITHOUT":
        query = query.filter(~Venue.offers.any())

    elif offer_status == "VALID" or offer_status == "EXPIRED":
        query = query.join(Offer)
        can_still_be_booked_event = Stock.bookingLimitDatetime >= datetime.utcnow()
        is_not_soft_deleted_thing = Stock.isSoftDeleted == False
        can_still_be_booked_thing = ((Stock.bookingLimitDatetime == None)
         | (Stock.bookingLimitDatetime >= datetime.utcnow()))
        is_available_thing = ((Stock.available == None) | (Stock.available > 0))

        query_1 = query.join(EventOccurrence).join(Stock)
        query_2 = query.join(Stock)

    if offer_status == "VALID":
        query_with_valid_event = query_1.filter(is_not_soft_deleted_thing
            & can_still_be_booked_thing & is_available_thing)
        query_with_valid_thing = query_2.filter(is_not_soft_deleted_thing
         & can_still_be_booked_thing & is_available_thing)
        query = query_with_valid_event.union_all(query_with_valid_thing)

    if offer_status == "EXPIRED":
        query_with_expired_event = query_1.filter(~(is_not_soft_deleted_thing
         & can_still_be_booked_thing & is_available_thing))
        query_with_expired_thing = query_2.filter(~(is_not_soft_deleted_thing
         & can_still_be_booked_thing & is_available_thing))
        query = query_with_expired_event.union_all(query_with_expired_thing)

    return query


def _filter_by_has_validated_user_offerer(query, has_validated_user_offerer):
    is_valid = UserOfferer.validationToken == None
    if has_validated_user_offerer:
        query = query.filter(Offerer.UserOfferers.any(is_valid))
    else:
        query = query.filter(~Offerer.UserOfferers.any(is_valid))
    return query


def _filter_by_has_validated_user(query, has_validated_user):
    is_valid = User.validationToken == None
    if has_validated_user:
        query = query.filter(Offerer.users.any(is_valid))
    else:
        query = query.filter(~Offerer.users.any(is_valid))
    return query

def filter_offerers_with_keywords_chain(query, keywords_chain):
    keywords_filter = create_filter_finding_all_keywords_in_at_least_one_of_the_models(
        offerer_ts_filter,
        keywords_chain
    )
    query = query.filter(keywords_filter)
    return query
