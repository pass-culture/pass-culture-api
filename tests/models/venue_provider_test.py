import pytest

from models import PcObject, Provider, ApiErrors
from tests.conftest import clean_database
from tests.test_utils import create_offerer, create_venue, create_offer_with_thing_product, \
    create_offer_with_event_product, create_venue_provider, create_provider, activate_provider


@clean_database
def test_nOffers_with_one_venue_provider(app):
    # given
    provider = create_provider('OpenAgenda')
    PcObject.save(provider)

    offerer = create_offerer()
    venue = create_venue(offerer)
    venue_provider = create_venue_provider(venue, provider)
    offer_1 = create_offer_with_thing_product(venue, last_provider_id=provider.id, id_at_providers='offer1')
    offer_2 = create_offer_with_event_product(venue, last_provider_id=provider.id, id_at_providers='offer2')
    offer_3 = create_offer_with_event_product(venue, last_provider_id=provider.id, id_at_providers='offer3')
    offer_4 = create_offer_with_thing_product(venue, last_provider_id=provider.id, id_at_providers='offer4')
    PcObject.save(offer_1, offer_2, offer_3, offer_4, venue_provider)

    # when
    n_offers = venue_provider.nOffers

    # then
    assert n_offers == 4


@clean_database
def test_nOffers_with_two_venue_providers_from_different_providers(app):
    # given
    provider1 = create_provider('OpenAgenda')
    provider2 = create_provider('TiteLive')
    PcObject.save(provider1, provider2)

    offerer = create_offerer()
    venue = create_venue(offerer)
    venue_provider1 = create_venue_provider(venue, provider1)
    venue_provider2 = create_venue_provider(venue, provider2)
    offer_1 = create_offer_with_thing_product(venue, last_provider_id=provider1.id, id_at_providers='offer1')
    offer_2 = create_offer_with_event_product(venue, last_provider_id=provider2.id, id_at_providers='offer2')
    offer_3 = create_offer_with_event_product(venue, last_provider_id=provider1.id, id_at_providers='offer3')
    offer_4 = create_offer_with_thing_product(venue, last_provider_id=provider1.id, id_at_providers='offer4')
    PcObject.save(offer_1, offer_2, offer_3, offer_4, venue_provider1, venue_provider2)

    # when
    n_offers_for_venue_provider1 = venue_provider1.nOffers
    n_offers_for_venue_provider2 = venue_provider2.nOffers

    # then
    assert n_offers_for_venue_provider1 == 3
    assert n_offers_for_venue_provider2 == 1


@clean_database
def test_raise_errors_if_venue_provider_already_exists_with_same_information(app):
    # given
    provider = activate_provider('TiteLiveStocks')
    offerer = create_offerer()
    venue = create_venue(offerer, name='Librairie Titelive', siret='77567146400110')
    venue_provider = create_venue_provider(venue, provider, venue_id_at_offer_provider="775671464")
    PcObject.save(venue_provider)

    venue_provider2 = create_venue_provider(venue, provider, venue_id_at_offer_provider="775671464")
    # when
    with pytest.raises(ApiErrors) as errors:
        PcObject.save(venue_provider2)

    # then
    assert errors.value.errors['global'] == ["Votre lieu est déjà lié à cette source"]
