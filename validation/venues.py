from decimal import Decimal, InvalidOperation

from models import ApiErrors

MAX_LONGITUDE = 180
MAX_LATITUDE = 90


def validate_coordinates(raw_latitude, raw_longitude):
    api_errors = ApiErrors()

    if raw_latitude:
        _validate_latitude(api_errors, raw_latitude)

    if raw_longitude:
        _validate_longitude(api_errors, raw_longitude)

    if api_errors.errors:
        raise api_errors


def check_valid_edition(managing_offerer_id):
    if managing_offerer_id:
        errors = ApiErrors()
        errors.addError('venue', 'Vous ne pouvez pas changer la structure d\'un lieu')
        raise errors


def _validate_longitude(api_errors, raw_longitude):
    try:
        longitude = Decimal(raw_longitude)
    except InvalidOperation:
        api_errors.addError('longitude', 'Format incorrect')
    else:
        if longitude > MAX_LONGITUDE or longitude < -MAX_LONGITUDE:
            api_errors.addError('longitude', 'La longitude doit être comprise entre -180.0 et +180.0')


def _validate_latitude(api_errors, raw_latitude):
    try:
        latitude = Decimal(raw_latitude)
    except InvalidOperation:
        api_errors.addError('latitude', 'Format incorrect')
    else:
        if latitude > MAX_LATITUDE or latitude < -MAX_LATITUDE:
            api_errors.addError('latitude', 'La latitude doit être comprise entre -90.0 et +90.0')
