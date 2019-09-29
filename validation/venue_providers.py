import json
from sqlalchemy_api_handler import ApiErrors, dehumanize

from repository.provider_queries import find_provider_by_id
from repository.venue_provider_queries import find_venue_provider


def _validate_existing_provider(provider_id: str):
    provider = find_provider_by_id(provider_id)
    is_provider_available_for_pro_usage = provider and provider.isActive and provider.enabledForPro
    if not is_provider_available_for_pro_usage:
        errors = ApiErrors()
        errors.status_code = 400
        errors.add_error('provider', "Cette source n'est pas disponible")
        raise errors


def _validate_existing_venue_provider(provider_id: int, venue_id: int, venue_id_at_offer_provider: str):
    is_existing_venue_provider = find_venue_provider(provider_id,
                                                     venue_id,
                                                     venue_id_at_offer_provider)
    if is_existing_venue_provider:
        errors = ApiErrors()
        errors.status_code = 400
        errors.add_error('venueProvider', "Votre lieu est déjà lié à cette source")
        raise errors


def validate_new_venue_provider_information(payload: json):
    errors = ApiErrors()
    errors.status_code = 400

    if 'venueIdAtOfferProvider' not in payload:
        errors.add_error('venueIdAtOfferProvider', 'Ce champ est obligatoire')
    if 'venueId' not in payload:
        errors.add_error('venueId', 'Ce champ est obligatoire')
    if 'providerId' not in payload:
        errors.add_error('providerId', 'Ce champ est obligatoire')

    errors.maybe_raise()

    provider_id = dehumanize(payload.get('providerId'))
    venue_id = dehumanize(payload.get('venueId'))
    venue_id_at_offer_provider = payload.get('venueIdAtOfferProvider')

    _validate_existing_provider(provider_id)
    _validate_existing_venue_provider(provider_id, venue_id, venue_id_at_offer_provider)
