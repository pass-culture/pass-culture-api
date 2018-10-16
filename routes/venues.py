""" venues """
from flask import current_app as app, jsonify, request
from flask_login import login_required

from models.user_offerer import RightsType
from models.venue import Venue
from repository.venue_queries import save_venue, save_venue_rib
from utils.file import has_file
from utils.includes import VENUE_INCLUDES
from utils.rest import ensure_current_user_has_rights, \
                       load_or_404
from validation.venues import check_valid_edition, \
                              validate_address, \
                              validate_bank_info, \
                              validate_coordinates

@app.route('/venues/<venueId>', methods=['GET'])
@login_required
def get_venue(venueId):
    venue = load_or_404(Venue, venueId)
    ensure_current_user_has_rights(RightsType.editor, venue.managingOffererId)
    return jsonify(venue._asdict(include=VENUE_INCLUDES))


@app.route('/venues', methods=['POST'])
@login_required
def create_venue():

    if request.json is not None:
        data = request.json
    else:
        data = request.form

    validate_coordinates(data.get('latitude', None), data.get('longitude', None))
    validate_address(data)
    validate_bank_info(data)

    venue = Venue(from_dict=data)
    venue.departementCode = 'XX'  # avoid triggerring check on this

    save_venue(venue)
    if data.get('iban'):
        save_venue_rib(venue)

    return jsonify(venue._asdict(include=VENUE_INCLUDES)), 201


@app.route('/venues/<venueId>', methods=['PATCH'])
@login_required
def edit_venue(venueId):

    if request.json is not None:
        data = request.json
    else:
        data = request.form

    venue = load_or_404(Venue, venueId)

    managing_offerer_id = data.get('managingOffererId')
    check_valid_edition(managing_offerer_id, venue)

    validate_coordinates(data.get('latitude', None), data.get('longitude', None))
    validate_address(data)
    ensure_current_user_has_rights(RightsType.editor, venue.managingOffererId)

    venue.populateFromDict(data)

    save_venue(venue)
    if has_file('rib'):
        save_venue_rib(venue)

    return jsonify(venue._asdict(include=VENUE_INCLUDES)), 200
