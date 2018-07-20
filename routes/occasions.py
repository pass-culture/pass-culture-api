"""occasions"""
from flask import current_app as app, jsonify, request
from flask_login import current_user

from utils.human_ids import dehumanize
from utils.includes import OCCASION_INCLUDES
from utils.rest import delete,\
                       ensure_current_user_has_rights,\
                       expect_json_data,\
                       handle_rest_get_list,\
                       load_or_404,\
                       login_or_api_key_required
from utils.search import get_search_filter


Event = app.model.Event
EventOccurence = app.model.EventOccurence
Occasion = app.model.Occasion
Offer = app.model.Offer
Offerer = app.model.Offerer
RightsType = app.model.RightsType
Thing = app.model.Thing
UserOfferer = app.model.UserOfferer
Venue = app.model.Venue



def create_event_occurence(json, occasion, offerer, venue):
    event_occurence = EventOccurence()
    event_occurence.event = occasion
    event_occurence.venue = venue
    event_occurence.populateFromDict(json, skipped_keys=['offer'])
    app.model.PcObject.check_and_save(event_occurence)

    offer = Offer()
    offer.eventOccurence = event_occurence
    offer.offerer = offerer
    offer.populateFromDict(json['offer'][0])
    app.model.PcObject.check_and_save(offer)


@app.route('/occasions', methods=['GET'])
@login_or_api_key_required
def list_occasions():
    offererId = dehumanize(request.args.get('offererId'))
    venueId = dehumanize(request.args.get('venueId'))
    query = Occasion.query

    if venueId is not None:
        venue = Venue.query.filter_by(id=venueId)\
                           .first_or_404()
        ensure_current_user_has_rights(RightsType.editor,
                                       venue.managingOffererId)
        query = query.filter_by(venue=venue)
    elif offererId is not None:
        ensure_current_user_has_rights(RightsType.editor,
                                       offererId)
        query = query.join(Venue)\
                     .join(Offerer)\
                     .filter_by(id=offererId)
    elif not current_user.isAdmin:
        query = query.join(Venue)\
                     .join(Offerer)\
                     .join(UserOfferer)\
                     .filter(UserOfferer.user == current_user)

    search = request.args.get('search')
    if search is not None:
        query = query.outerjoin(Event)\
                     .outerjoin(Thing)\
                     .filter(get_search_filter([Event, Thing], search))

    return handle_rest_get_list(Occasion,
                                include=OCCASION_INCLUDES,
                                query=query,
                                page=request.args.get('page'),
                                paginate=10,
                                order_by='occasion.id desc')


@app.route('/occasions/<id>', methods=['GET'])
@login_or_api_key_required
def get_occasion(id):
    occasion = load_or_404(Occasion, id)
    return jsonify(occasion._asdict(include=OCCASION_INCLUDES))

@app.route('/occasions', methods=['POST'])
@login_or_api_key_required
@expect_json_data
def post_occasion():
    ocas = Occasion()
    venue = load_or_404(Venue, request.json['venueId'])
    ensure_current_user_has_rights(RightsType.editor,
                                   venue.managingOffererId)
    ocas.populateFromDict(request.json)
    app.model.PcObject.check_and_save(ocas)
    return jsonify(ocas._asdict(include=OCCASION_INCLUDES)), 201

@app.route('/occasions/<id>', methods=['DELETE'])
@login_or_api_key_required
def delete_occasion(id):
    ocas = load_or_404(Occasion, id)
    ensure_current_user_has_rights(app.model.RightsType.editor,
                                   ocas.venue.managingOffererId)
    return delete(ocas)
