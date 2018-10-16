from decimal import Decimal, InvalidOperation

from models import ApiErrors
from utils.file import has_file
from utils.human_ids import dehumanize

MAX_LONGITUDE = 180
MAX_LATITUDE = 90

def validate_bank_info(data):
    api_errors = ApiErrors()
    if data.get('bic') and not data.get('iban'):
        api_errors.addError('iban', "Il manque l'iban associé à votre bic")
        raise api_errors
    if data.get('iban') and not data.get('bic'):
        api_errors.addError('bic', "Il manque le bic associé à votre iban")
        raise api_errors
    if data.get('iban') and not has_file('rib'):
        api_errors.addError('rib', "Vous devez fournir un justificatif de rib")
        raise api_errors

def validate_address(data):
    api_errors = ApiErrors()
    if 'postalCode' in data and data['postalCode'] is None:
        api_errors.addError('postalCode', "Le code postal est obligatoire")
        raise api_errors
    if 'city' in data and data['city'] is None:
        api_errors.addError('city', "La ville est obligatoire")
        raise api_errors

def validate_coordinates(raw_latitude, raw_longitude):
    api_errors = ApiErrors()

    if raw_latitude:
        _validate_latitude(api_errors, raw_latitude)

    if raw_longitude:
        _validate_longitude(api_errors, raw_longitude)

    if api_errors.errors:
        raise api_errors


def check_valid_edition(managing_offerer_id, venue):
    if managing_offerer_id and dehumanize(managing_offerer_id) != venue.id:
        errors = ApiErrors()
        errors.addError('managingOffererId', 'Vous ne pouvez pas changer la structure d\'un lieu')
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
