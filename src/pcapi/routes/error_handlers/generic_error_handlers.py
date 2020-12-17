from typing import Dict
from typing import Tuple
from typing import Union

from flask import current_app as app
from flask import jsonify
from flask import request
import simplejson as json
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.exceptions import NotFound

import pcapi.core.offers.exceptions as offers_exceptions
from pcapi.domain.identifier.identifier import NonProperlyFormattedScrambledId
from pcapi.domain.user_activation import AlreadyActivatedException
from pcapi.models.api_errors import ApiErrors
from pcapi.models.api_errors import DateTimeCastError
from pcapi.models.api_errors import DecimalCastError
from pcapi.utils.human_ids import NonDehumanizableId


@app.errorhandler(NotFound)
def restize_not_found_route_errors(error: NotFound) -> Tuple[Dict, int]:
    return {}, 404


@app.errorhandler(ApiErrors)
def restize_api_errors(error: ApiErrors) -> Tuple[Dict, int]:
    return jsonify(error.errors), error.status_code or 400


@app.errorhandler(offers_exceptions.TooLateToDeleteStock)
def restize_too_late_to_delete_stock(error: offers_exceptions.TooLateToDeleteStock) -> Tuple[Dict, int]:
    return jsonify(error.errors), 400


@app.errorhandler(Exception)
def internal_error(error: Exception) -> Union[Tuple[Dict, int], HTTPException]:
    # pass through HTTP errors
    if isinstance(error, HTTPException):
        return error
    app.logger.exception("Unexpected error on method=%s url=%s: %s", request.method, request.url, error)
    errors = ApiErrors()
    errors.add_error("global", "Il semble que nous ayons des problèmes techniques :(" + " On répare ça au plus vite.")
    return jsonify(errors.errors), 500


@app.errorhandler(MethodNotAllowed)
def method_not_allowed(error: MethodNotAllowed) -> Tuple[Dict, int]:
    api_errors = ApiErrors()
    api_errors.add_error("global", "La méthode que vous utilisez n'existe pas sur notre serveur")
    app.logger.error("405 %s" % str(error))
    return jsonify(api_errors.errors), 405


@app.errorhandler(NonProperlyFormattedScrambledId)
@app.errorhandler(NonDehumanizableId)
def invalid_id_for_dehumanize_error(error: NonDehumanizableId) -> Tuple[Dict, int]:
    api_errors = ApiErrors()
    api_errors.add_error("global", "La page que vous recherchez n'existe pas")
    app.logger.error("404 %s" % str(error))
    return jsonify(api_errors.errors), 404


@app.errorhandler(DecimalCastError)
def decimal_cast_error(error: DecimalCastError) -> Tuple[Dict, int]:
    api_errors = ApiErrors()
    app.logger.warning(json.dumps(error.errors))
    for field in error.errors.keys():
        api_errors.add_error(field, "Saisissez un nombre valide")
    return jsonify(api_errors.errors), 400


@app.errorhandler(DateTimeCastError)
def date_time_cast_error(error: DateTimeCastError) -> Tuple[Dict, int]:
    api_errors = ApiErrors()
    app.logger.warning(json.dumps(error.errors))
    for field in error.errors.keys():
        api_errors.add_error(field, "Format de date invalide")
    return jsonify(api_errors.errors), 400


@app.errorhandler(AlreadyActivatedException)
def already_activated_exception(error: AlreadyActivatedException) -> Tuple[Dict, int]:
    app.logger.error(json.dumps(error.errors))
    return jsonify(error.errors), 405
