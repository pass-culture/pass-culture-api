import subprocess
from flask import current_app as app, jsonify, request
from sqlalchemy_api_handler import ApiErrors, ApiHandler, as_dict, dehumanize, load_or_404

from models.venue_provider import VenueProvider
from utils.config import API_ROOT_PATH
from utils.includes import VENUE_PROVIDER_INCLUDES
from utils.rest import expect_json_data, \
    login_or_api_key_required
from validation.venue_providers import validate_new_venue_provider_information


@app.route('/venueProviders', methods=['GET'])
@login_or_api_key_required
def list_venue_providers():
    venue_id = request.args.get('venueId')
    if venue_id is None:
        e = ApiErrors()
        e.add_error('venueId', 'Vous devez obligatoirement fournir le paramètre venueId')
        return jsonify(e.errors), 400

    vp_query = VenueProvider.query \
        .filter_by(venueId=dehumanize(venue_id))
    return jsonify([
        as_dict(venue_provider, includes=VENUE_PROVIDER_INCLUDES)
        for venue_provider in vp_query.all()
    ])


@app.route('/venueProviders/<id>', methods=['GET'])
@login_or_api_key_required
def get_venue_provider(id):
    venue_provider = load_or_404(VenueProvider, id)
    return jsonify(as_dict(venue_provider, includes=VENUE_PROVIDER_INCLUDES))


@app.route('/venueProviders', methods=['POST'])
@login_or_api_key_required
@expect_json_data
def create_venue_provider():
    venue_provider_payload = request.json
    validate_new_venue_provider_information(venue_provider_payload)

    new_venue_provider = VenueProvider(**venue_provider_payload)
    ApiHandler.save(new_venue_provider)

    subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                     + ' --venue-provider-id %s' % str(new_venue_provider.id),
                     shell=True,
                     cwd=API_ROOT_PATH)

    return jsonify(as_dict(new_venue_provider, includes=VENUE_PROVIDER_INCLUDES)), 201
