import subprocess

from flask import current_app as app
from flask import jsonify, request
from flask_login import login_required

import local_providers
from domain.stock_provider.stock_provider_repository import StockProviderRepository
from infrastructure.container import api_fnac_stocks, api_libraires_stocks, api_praxiel_stocks, api_titelive_stocks
from local_providers import FnacStocks, LibrairesStocks, PraxielStocks, AllocineStocks
from local_providers.titelive_stocks.titelive_stocks import TiteLiveStocks
from models.api_errors import ApiErrors
from models.venue_provider import VenueProvider
from repository.allocine_pivot_queries import get_allocine_theaterId_for_venue
from repository.venue_queries import find_by_id
from repository.provider_queries import get_provider_enabled_for_pro_by_id
from routes.serialization import as_dict
from use_cases.connect_venue_to_allocine import connect_venue_to_allocine
from use_cases.connect_venue_to_provider import connect_venue_to_provider
from utils.config import API_ROOT_PATH
from utils.human_ids import dehumanize
from utils.includes import VENUE_PROVIDER_INCLUDES
from utils.rest import expect_json_data, load_or_404
from validation.routes.venue_providers import check_existing_provider, check_new_venue_provider_information


@app.route('/venueProviders', methods=['GET'])
@login_required
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
@login_required
def get_venue_provider(id):
    venue_provider = load_or_404(VenueProvider, id)
    return jsonify(as_dict(venue_provider, includes=VENUE_PROVIDER_INCLUDES))


@app.route('/venueProviders', methods=['POST'])
@login_required
@expect_json_data
def create_venue_provider():
    venue_provider_payload = request.json
    check_new_venue_provider_information(venue_provider_payload)

    provider_id = dehumanize(venue_provider_payload['providerId'])
    provider = get_provider_enabled_for_pro_by_id(provider_id)
    check_existing_provider(provider)

    provider_class = getattr(local_providers, provider.localClass)
    if provider_class == AllocineStocks:
        new_venue_provider = connect_venue_to_allocine(venue_provider_payload,
                                                       find_by_id,
                                                       get_allocine_theaterId_for_venue)
    else:
        stock_provider_repository = _get_stock_provider_repository(provider_class)
        new_venue_provider = connect_venue_to_provider(provider_class,
                                                       stock_provider_repository,
                                                       venue_provider_payload,
                                                       find_by_id)

    _run_first_synchronization(new_venue_provider)

    return jsonify(as_dict(new_venue_provider, includes=VENUE_PROVIDER_INCLUDES)), 201


def _get_stock_provider_repository(provider_class) -> StockProviderRepository:
    providers = {
        LibrairesStocks: api_libraires_stocks,
        FnacStocks: api_fnac_stocks,
        TiteLiveStocks: api_titelive_stocks,
        PraxielStocks: api_praxiel_stocks
    }
    return providers.get(provider_class, None)


def _run_first_synchronization(new_venue_provider: VenueProvider):
    subprocess.Popen('PYTHONPATH="." python scripts/pc.py update_providables'
                     + ' --venue-provider-id %s' % str(new_venue_provider.id),
                     shell=True,
                     cwd=API_ROOT_PATH)
