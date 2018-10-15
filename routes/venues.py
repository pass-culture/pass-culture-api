""" venues """
from flask import current_app as app, jsonify, request
from flask_login import login_required

from models.api_errors import ApiErrors
from models.user_offerer import RightsType
from models.venue import Venue
from repository.venue_queries import save_venue
from utils.file import has_file, read_file
from utils.includes import VENUE_INCLUDES
from utils.rest import ensure_current_user_has_rights, \
    expect_json_data, \
    load_or_404
from validation.venues import validate_coordinates, check_valid_edition


@app.route('/venues/<venueId>', methods=['GET'])
@login_required
def get_venue(venueId):
    venue = load_or_404(Venue, venueId)
    ensure_current_user_has_rights(RightsType.editor, venue.managingOffererId)
    return jsonify(venue._asdict(include=VENUE_INCLUDES))


@app.route('/venues', methods=['POST'])
@login_required
def create_venue():


    print('request.json', request.json)
    if request.json is not None:
        data = request.json
    else:
        data = request.form

    print('data', data)

    validate_coordinates(data.get('latitude', None), data.get('longitude', None))

    api_errors = ApiErrors()
    if data.get('bic') and not data.get('iban'):
        api_errors.addError('iban', "Il manque l'iban associé à votre bic")
        return jsonify(api_errors.errors), 400
    if data.get('iban') and not data.get('bic'):
        api_errors.addError('bic', "Il manque le bic associé à votre iban")
        return jsonify(api_errors.errors), 400
    if data.get('iban') and not has_file('rib_pdf'):
        api_errors.addError('rib_pdf', "Vous devez fournir un justificatif de rib")
        return jsonify(api_errors.errors), 400

    venue = Venue(from_dict=data)
    venue.departementCode = 'XX'  # avoid triggerring check on this
    save_venue(venue)

    if data.get('iban'):
        try:
            venue.save_thumb(read_file('rib'), 0)
        except ValueError as e:
            logger.error(e)
            api_errors.addError('rib_pdf', "Le rib pdf n'est pas au bon format")
            raise api_errors

    return jsonify(venue._asdict(include=VENUE_INCLUDES)), 201


@app.route('/venues/<venueId>', methods=['PATCH'])
@login_required
@expect_json_data
def edit_venue(venueId):
    managing_offerer_id = request.json.get('managingOffererId')
    check_valid_edition(managing_offerer_id)
    venue = load_or_404(Venue, venueId)
    validate_coordinates(request.json.get('latitude', None), request.json.get('longitude', None))
    ensure_current_user_has_rights(RightsType.editor, venue.managingOffererId)
    venue.populateFromDict(request.json)
    save_venue(venue)
    return jsonify(venue._asdict(include=VENUE_INCLUDES)), 200
