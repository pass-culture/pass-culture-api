from flask import current_app as app, jsonify, request
from flask_login import current_user, login_required

from domain.admin_emails import send_offer_creation_notification_to_support
from models import Offer, PcObject, Venue, Event, Thing, RightsType
from models.api_errors import ResourceNotFound
from repository import venue_queries, offer_queries, thing_queries, event_queries
from repository.offer_queries import find_activation_offers, \
    find_offers_with_filter_parameters
from repository.recommendation_queries import invalidate_recommendations
from utils.config import PRO_URL
from utils.human_ids import dehumanize
from utils.includes import OFFER_INCLUDES
from utils.mailing import send_raw_email
from utils.rest import expect_json_data, \
    handle_rest_get_list, \
    load_or_404, login_or_api_key_required, load_or_raise_error, ensure_current_user_has_rights
from validation.events import check_has_venue_id, check_user_can_create_activation_event
from validation.offers import check_venue_exists_when_requested, check_user_has_rights_for_query, check_valid_edition
from validation.url import is_url_safe


@app.route('/offers', methods=['GET'])
@login_required
def list_offers():
    offerer_id = dehumanize(request.args.get('offererId'))
    venue_id = dehumanize(request.args.get('venueId'))
    venue = venue_queries.find_by_id(venue_id)

    check_venue_exists_when_requested(venue, venue_id)
    check_user_has_rights_for_query(offerer_id, venue, venue_id)

    query = find_offers_with_filter_parameters(
        current_user,
        offerer_id=offerer_id,
        venue_id=venue_id,
        keywords_string=request.args.get('keywords')
    )

    return handle_rest_get_list(Offer,
                                include=OFFER_INCLUDES,
                                page=request.args.get('page'),
                                paginate=10,
                                order_by='offer.id desc',
                                query=query)


@app.route('/offers/activation', methods=['GET'])
@login_required
def list_activation_offers():
    departement_code = current_user.departementCode
    query = find_activation_offers(departement_code)

    return handle_rest_get_list(
        Offer,
        include=OFFER_INCLUDES,
        query=query
    )


@app.route('/offers/<id>', methods=['GET'])
@login_required
def get_offer(id):
    offer = load_or_404(Offer, id)
    return jsonify(offer._asdict(include=OFFER_INCLUDES))


@app.route('/offers', methods=['POST'])
@login_or_api_key_required
@expect_json_data
def post_offer():
    venue_id = request.json.get('venueId')
    check_has_venue_id(venue_id)
    venue = load_or_raise_error(Venue, venue_id)
    ensure_current_user_has_rights(RightsType.editor, venue.managingOffererId)
    thing_dict = request.json.get('thing')
    event_dict = request.json.get('event')
    event_id = dehumanize(request.json.get('eventId'))
    thing_id = dehumanize(request.json.get('thingId'))
    if event_dict:
        offer = _fill_offer_with_new_event_data(event_dict)

    elif thing_dict:
        offer = _fill_offer_with_new_thing_data(thing_dict)

    elif thing_id:
        offer = _fill_offer_with_existing_thing_data(thing_id)

    elif event_id:
        offer = _fill_offer_with_existing_event_data(event_id)

    offer.venue = venue
    offer.bookingEmail = request.json.get('bookingEmail', None)
    PcObject.check_and_save(offer)
    send_offer_creation_notification_to_support(offer, current_user, PRO_URL, send_raw_email)

    return jsonify(
        offer._asdict(include=OFFER_INCLUDES)
    ), 201


@app.route('/offer/<id>', methods=['PATCH'])
@login_or_api_key_required
@expect_json_data
def patch_offer(id):
    thing_or_event_dict = request.json.get('thing') or request.json.get('event')
    check_valid_edition(request.json, thing_or_event_dict)
    offer = offer_queries.find_offer_by_id(dehumanize(id))
    if not offer:
        raise ResourceNotFound
    ensure_current_user_has_rights(RightsType.editor, offer.venue.managingOffererId)
    offer.populateFromDict(request.json)
    if thing_or_event_dict:
        _update_offer_with_thing_or_event_data(offer, thing_or_event_dict)
    PcObject.check_and_save(offer)
    if 'isActive' in request.json and not request.json['isActive']:
        invalidate_recommendations(offer)

    return jsonify(
        offer._asdict(include=OFFER_INCLUDES)
    ), 200


def _update_offer_with_thing_or_event_data(offer: Offer, thing_or_event_dict: dict):
    offer.populateFromDict(thing_or_event_dict)
    owning_offerer = offer.eventOrThing.owningOfferer
    if owning_offerer and owning_offerer == offer.venue.managingOfferer:
        offer.eventOrThing.populateFromDict(thing_or_event_dict)


def _fill_offer_with_new_thing_data(thing_dict: str) -> Offer:
    thing = Thing()
    url = thing_dict.get('url')
    if url:
        is_url_safe(url)
        thing_dict['isNational'] = True
    thing.populateFromDict(thing_dict)
    offer = Offer()
    offer.populateFromDict(thing_dict)
    offer.thing = thing
    return offer


def _fill_offer_with_new_event_data(event_dict: dict) -> Offer:
    event = Event()
    event.populateFromDict(event_dict)
    check_user_can_create_activation_event(current_user, event)
    offer = Offer()
    offer.populateFromDict(event_dict)
    offer.event = event
    return offer


def _fill_offer_with_existing_thing_data(thing_id: str) -> Offer:
    thing = thing_queries.find_by_id(thing_id)
    offer = Offer()
    offer.populateFromDict(request.json)
    offer.thing = thing
    offer.type = thing.type
    offer.name = thing.name
    offer.description = thing.description
    offer.url = thing.url
    offer.mediaUrls = thing.mediaUrls
    offer.isNational = thing.isNational
    offer.extraData = thing.extraData
    return offer


def _fill_offer_with_existing_event_data(event_id: str) -> Offer:
    offer = Offer()
    event = event_queries.find_by_id(event_id)
    offer.event = event
    offer.type = event.type
    offer.name = event.name
    offer.description = event.description
    offer.mediaUrls = event.mediaUrls
    offer.conditions = event.conditions
    offer.ageMin = event.ageMin
    offer.ageMax = event.ageMax
    offer.accessibility = event.accessibility
    offer.durationMinutes = event.durationMinutes
    offer.isNational = event.isNational
    offer.extraData = event.extraData
    return offer
