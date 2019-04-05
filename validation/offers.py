from flask import Request

from models import RightsType
from models.api_errors import ResourceNotFound, ApiErrors
from models.offer_type import ProductType
from utils.rest import ensure_current_user_has_rights


def check_user_has_rights_for_query(offerer_id, venue, venue_id):
    if venue_id:
        ensure_current_user_has_rights(RightsType.editor,
                                       venue.managingOffererId)
    elif offerer_id:
        ensure_current_user_has_rights(RightsType.editor,
                                       offerer_id)


def check_has_venue_id(venue_id):
    if venue_id is None:
        api_errors = ApiErrors()
        api_errors.addError('venueId', 'Vous devez préciser un identifiant de lieu')
        raise api_errors


def check_venue_exists_when_requested(venue, venue_id):
    if venue_id and venue is None:
        errors = ResourceNotFound()
        errors.addError(
            'global',
            "Ce lieu n'a pas été trouvé"
        )
        raise errors


def check_valid_edition(request: Request, thing_or_event_dict: dict):
    forbidden_keys = {'idAtProviders', 'dateModifiedAtLastProvider', 'thumbCount', 'firstThumbDominantColor',
                      'owningOffererId', 'id', 'lastProviderId', 'isNational', 'dateCreated'}
    all_keys = request.keys()
    if thing_or_event_dict:
        all_keys = set(all_keys).union(set(thing_or_event_dict.keys()))
    keys_in_error = forbidden_keys.intersection(all_keys)
    if thing_or_event_dict and keys_in_error:
        errors = ApiErrors()
        for key in keys_in_error:
            errors.addError(key, 'Vous ne pouvez pas modifier cette information')
        raise errors


def check_offer_type_is_valid(offer_type_name):

    if not ProductType.is_thing(offer_type_name) and not ProductType.is_event(offer_type_name):
        api_error = ApiErrors()
        api_error.addError('type',
                           'Le type de cette offre est inconnu')
        raise api_error
