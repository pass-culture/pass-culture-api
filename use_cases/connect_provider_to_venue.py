from decimal import Decimal
from typing import Dict, Optional

from domain.price_rule import PriceRule
from domain.stock_provider.stock_provider_repository import StockProviderRepository
from local_providers import AllocineStocks, FnacStocks, LibrairesStocks, TiteLiveStocks
from models import AllocineVenueProvider, AllocineVenueProviderPriceRule, ApiErrors, VenueProvider, VenueSQLEntity
from repository import repository
from repository.allocine_pivot_queries import get_allocine_theaterId_for_venue
from repository.venue_queries import find_by_id
from utils.human_ids import dehumanize
from validation.routes.venues import check_existing_venue

STANDARDIZED_PROVIDERS = [LibrairesStocks, TiteLiveStocks, FnacStocks]
ERROR_CODE_PROVIDER_NOT_SUPPORTED = 400
ERROR_CODE_SIRET_NOT_SUPPORTED = 422


def connect_provider_to_venue(provider_class,
                              stock_repository: StockProviderRepository,
                              venue_provider_payload: Dict) -> VenueProvider:
    venue_id = dehumanize(venue_provider_payload['venueId'])
    venue = find_by_id(venue_id)
    check_existing_venue(venue)
    if provider_class == AllocineStocks:
        new_venue_provider = _connect_allocine_to_venue(venue, venue_provider_payload)
    elif provider_class in STANDARDIZED_PROVIDERS:
        check_venue_can_be_synchronized_with_provider(venue, stock_repository, provider_class.name)
        new_venue_provider = _connect_standardized_providers_to_venue(venue, venue_provider_payload)
    else:
        errors = ApiErrors()
        errors.status_code = ERROR_CODE_PROVIDER_NOT_SUPPORTED
        errors.add_error('provider', 'Provider non pris en charge')
        raise errors

    return new_venue_provider


def _connect_allocine_to_venue(venue: VenueSQLEntity, payload: Dict) -> AllocineVenueProvider:
    allocine_theater_id = get_allocine_theaterId_for_venue(venue)
    allocine_venue_provider = _create_allocine_venue_provider(allocine_theater_id, payload, venue)
    allocine_venue_provider_price_rule = _create_allocine_venue_provider_price_rule(allocine_venue_provider,
                                                                                    payload.get('price'))

    repository.save(allocine_venue_provider_price_rule)

    return allocine_venue_provider


def _connect_standardized_providers_to_venue(venue: VenueSQLEntity, payload: Dict) -> VenueProvider:
    venue_provider = VenueProvider()
    venue_provider.venue = venue
    venue_provider.providerId = dehumanize(payload['providerId'])
    venue_provider.venueIdAtOfferProvider = venue.siret

    repository.save(venue_provider)
    return venue_provider


def _create_allocine_venue_provider_price_rule(allocine_venue_provider: VenueProvider,
                                               price: Decimal) -> AllocineVenueProviderPriceRule:
    venue_provider_price_rule = AllocineVenueProviderPriceRule()
    venue_provider_price_rule.allocineVenueProvider = allocine_venue_provider
    venue_provider_price_rule.priceRule = PriceRule.default
    venue_provider_price_rule.price = price

    return venue_provider_price_rule


def _create_allocine_venue_provider(allocine_theater_id: str, payload: Dict,
                                    venue: VenueSQLEntity) -> AllocineVenueProvider:
    allocine_venue_provider = AllocineVenueProvider()
    allocine_venue_provider.venue = venue
    allocine_venue_provider.providerId = dehumanize(payload['providerId'])
    allocine_venue_provider.venueIdAtOfferProvider = allocine_theater_id
    allocine_venue_provider.isDuo = payload.get('isDuo')
    allocine_venue_provider.quantity = payload.get('quantity')

    return allocine_venue_provider


def check_venue_can_be_synchronized_with_provider(venue: VenueSQLEntity,
                                                  stock_repository: StockProviderRepository,
                                                  name: str) -> None:
    if not venue.siret or not stock_repository.can_be_synchronized(venue.siret):
        errors = ApiErrors()
        errors.status_code = ERROR_CODE_SIRET_NOT_SUPPORTED
        errors.add_error('provider', _get_synchronization_error_message(name, venue.siret))
        raise errors


def _get_synchronization_error_message(provider_name: str, siret: Optional[str]) -> str:
    if siret:
        return f'L’importation d’offres avec {provider_name} n’est pas disponible pour le SIRET {siret}'
    else:
        return f'L’importation d’offres avec {provider_name} n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres.'
