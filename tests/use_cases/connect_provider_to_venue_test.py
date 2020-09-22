from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.repository.stock_provider.stock_provider_libraires import StockProviderLibrairesRepository
from local_providers import AllocineStocks, FnacStocks, LibrairesStocks, TiteLiveStocks
from models import AllocineVenueProvider, AllocineVenueProviderPriceRule, ApiErrors, VenueProvider
from repository import repository
from tests.conftest import clean_database
from tests.local_providers.provider_test_utils import TestLocalProvider
from tests.model_creators.generic_creators import create_offerer, create_provider, create_venue
from tests.model_creators.provider_creators import activate_provider
from use_cases.connect_provider_to_venue import connect_provider_to_venue
from utils.human_ids import humanize


class UseCaseTest:
    class ConnectProviderToVenueTest:
        class WhenProviderIsAllocine:
            @clean_database
            def test_should_connect_venue_to_allocine_provider(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer)
                provider = activate_provider('AllocineStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                provider_type = AllocineStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                    'price': '9.99',
                    'isDuo': True,
                    'quantity': 50
                }

                # When
                connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # Then
                allocine_venue_provider = AllocineVenueProvider.query.one()
                venue_provider_price_rule = AllocineVenueProviderPriceRule.query.one()

                assert allocine_venue_provider.venue == venue
                assert allocine_venue_provider.isDuo
                assert allocine_venue_provider.quantity == 50
                assert venue_provider_price_rule.price == Decimal('9.99')

        class WhenProviderIsLibraires:
            @clean_database
            def test_should_connect_venue_to_libraires_provider(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer)
                provider = activate_provider('LibrairesStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                stock_repository.can_be_synchronized.return_value = True
                provider_type = LibrairesStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # When
                connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # Then
                libraires_venue_provider = VenueProvider.query.one()
                assert libraires_venue_provider.venue == venue

            @clean_database
            def test_should_not_connect_venue_to_libraires_provider_if_not_interfaced(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer, siret='12345678912345')
                provider = activate_provider('LibrairesStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                stock_repository.can_be_synchronized.return_value = False
                provider_class = LibrairesStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # when
                with pytest.raises(ApiErrors) as error:
                    print(connect_provider_to_venue(provider_class, stock_repository, venue_provider_payload))

                # then
                assert error.value.errors['provider'] == [
                    'L’importation d’offres avec LesLibraires n’est pas disponible pour le SIRET 12345678912345']

            @clean_database
            def test_should_not_connect_venue_to_libraires_provider_if_venue_has_no_siret(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer, siret=None, is_virtual=True)
                provider = activate_provider('LibrairesStocks')
                stock_repository = MagicMock(StockProviderLibrairesRepository)

                repository.save(venue)

                stock_repository = MagicMock()
                provider_type = LibrairesStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # when
                with pytest.raises(ApiErrors) as error:
                    connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # then
                assert error.value.errors['provider'] == [
                    'L’importation d’offres avec LesLibraires n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres.']

        class WhenProviderIsTiteLive:
            @clean_database
            @patch('use_cases.connect_provider_to_venue.can_be_synchronized_with_titelive')
            def test_should_connect_venue_to_titelive_provider(self, stubbed_can_by_synchronized, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer)
                provider = activate_provider('TiteLiveStocks')

                repository.save(venue)

                provider_type = TiteLiveStocks
                stock_repository = None
                stubbed_can_by_synchronized.return_value = True

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # When
                connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # Then
                titelive_venue_provider = VenueProvider.query.one()
                assert titelive_venue_provider.venue == venue

            @clean_database
            @patch('use_cases.connect_provider_to_venue.can_be_synchronized_with_titelive')
            def test_should_not_connect_venue_to_titelive_provider_if_not_interfaced(self, stubbed_can_by_synchronized,
                                                                                     app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer, siret='12345678912345')
                provider = activate_provider('TiteLiveStocks')

                repository.save(venue)

                stock_repository = None
                provider_type = TiteLiveStocks

                stubbed_can_by_synchronized.return_value = False
                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # when
                with pytest.raises(ApiErrors) as error:
                    connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # then
                assert error.value.errors['provider'] == [
                    'L’importation d’offres avec TiteLive'
                    ' n’est pas disponible pour le SIRET 12345678912345']

            @clean_database
            def test_should_not_connect_venue_to_titelive_provider_if_venue_has_no_siret(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer, siret=None, is_virtual=True)
                provider = activate_provider('TiteLiveStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                stock_repository.can_be_synchronized.return_value = True
                provider_type = TiteLiveStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # when
                with pytest.raises(ApiErrors) as error:
                    connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # then
                assert error.value.errors['provider'] == [
                    'L’importation d’offres avec TiteLive n’est '
                    'pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres.']

        class WhenProviderIsFnac:
            @clean_database
            def test_should_connect_venue_to_fnac_provider(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer)
                provider = activate_provider('FnacStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                stock_repository.can_be_synchronized.return_value = True
                provider_type = FnacStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # When
                connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # Then
                fnac_venue_provider = VenueProvider.query.one()
                assert fnac_venue_provider.venue == venue

            @clean_database
            def test_should_not_connect_venue_to_fnac_provider_if_not_interfaced(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer, siret='12345678912345')
                provider = activate_provider('FnacStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                stock_repository.can_be_synchronized.return_value = False
                provider_type = FnacStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # when
                with pytest.raises(ApiErrors) as error:
                    connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # then
                assert error.value.errors['provider'] == [
                    'L’importation d’offres avec FNAC n’est pas disponible pour le SIRET 12345678912345']

            @clean_database
            def test_should_not_connect_venue_to_fnac_provider_if_venue_has_no_siret(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer, siret=None, is_virtual=True)
                provider = activate_provider('FnacStocks')

                repository.save(venue)

                stock_repository = MagicMock()
                provider_type = FnacStocks

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # when
                with pytest.raises(ApiErrors) as error:
                    connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # then
                assert error.value.errors['provider'] == [
                    'L’importation d’offres avec FNAC n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres.']

        class WhenProviderIsSomethingElse:
            @clean_database
            def test_should_raise_an_error(self, app):
                # Given
                offerer = create_offerer()
                venue = create_venue(offerer)
                provider = create_provider(local_class='TestLocalProvider')
                repository.save(venue, provider)

                stock_repository = MagicMock()
                provider_type = TestLocalProvider

                venue_provider_payload = {
                    'providerId': humanize(provider.id),
                    'venueId': humanize(venue.id),
                }

                # When
                with pytest.raises(ApiErrors) as error:
                    connect_provider_to_venue(provider_type, stock_repository, venue_provider_payload)

                # Then
                assert error.value.errors['provider'] == ['Provider non pris en charge']
