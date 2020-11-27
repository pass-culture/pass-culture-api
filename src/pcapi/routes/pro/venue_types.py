from flask import jsonify
from flask_login import login_required

from pcapi.flask_app import private_api
from pcapi.repository.venue_types_queries import get_all_venue_types
from pcapi.routes.serialization import as_dict
from pcapi.use_cases.get_types_of_venues import get_types_of_venues


# @debt api-migration
@private_api.route("/venue-types", methods=["GET"])
@login_required
def get_venue_types():
    types_of_venues = get_types_of_venues(get_all_venue_types)

    return jsonify([as_dict(type) for type in types_of_venues]), 200
