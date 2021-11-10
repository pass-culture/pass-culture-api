from decimal import Decimal

import pytest

from pcapi.core.offerers.factories import AllocineVenueProviderFactory
from pcapi.core.offerers.factories import AllocineVenueProviderPriceRuleFactory
from pcapi.core.offers.factories import VenueFactory
from pcapi.core.providers.models import AllocineVenueProviderPriceRule
from pcapi.domain.price_rule import PriceRule
from pcapi.scripts.venue.modify_allocine_price_rule_for_venue import modify_allocine_price_rule_for_venue_by_id
from pcapi.scripts.venue.modify_allocine_price_rule_for_venue import modify_allocine_price_rule_for_venue_by_siret


class ModifyAllocinePriceRuleForVenueTest:
    @pytest.mark.usefixtures("db_session")
    def should_update_allocine_price_rule_for_venue_with_given_id(self, app):
        # Given
        initial_price = Decimal(7.5)
        new_price = Decimal(8)
        venue = VenueFactory()
        allocine_venue_provider = AllocineVenueProviderFactory(venue=venue)
        allocine_venue_provider_price_rule = AllocineVenueProviderPriceRuleFactory(
            allocineVenueProvider=allocine_venue_provider, priceRule=PriceRule.default, price=initial_price
        )

        # When
        modify_allocine_price_rule_for_venue_by_id(venue.id, new_price)

        # Then
        assert allocine_venue_provider_price_rule.price == new_price

    @pytest.mark.usefixtures("db_session")
    def should_update_allocine_price_rule_for_venue_with_given_siret(self, app):
        # Given
        initial_price = Decimal(7.5)
        new_price = Decimal(8)
        allocine_venue_provider_price_rule = AllocineVenueProviderPriceRuleFactory(
            priceRule=PriceRule.default, price=initial_price
        )
        venue = allocine_venue_provider_price_rule.allocineVenueProvider.venue

        # When
        modify_allocine_price_rule_for_venue_by_siret(venue.siret, new_price)

        # Then
        assert allocine_venue_provider_price_rule.price == new_price

    @pytest.mark.usefixtures("db_session")
    def should_not_update_allocine_price_rule_when_there_is_no_venue_provider_associated_to_the_venue(self, app):
        # Given
        new_price = Decimal(8)
        venue = VenueFactory()

        # When
        modify_allocine_price_rule_for_venue_by_siret(venue.siret, new_price)

        # Then
        assert AllocineVenueProviderPriceRule.query.count() == 0

    @pytest.mark.usefixtures("db_session")
    def should_not_update_allocine_price_rule_when_there_is_no_allocine_price_rule_associated_to_the_venue(self, app):
        # Given
        new_price = Decimal(8)
        venue = VenueFactory()
        AllocineVenueProviderFactory(venue=venue)

        # When
        modify_allocine_price_rule_for_venue_by_siret(venue.siret, new_price)

        # Then
        assert AllocineVenueProviderPriceRule.query.count() == 0
