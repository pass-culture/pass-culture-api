from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import pcapi.core.offerers.factories as offerers_factories
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_provider
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.provider_creators import activate_provider
from pcapi.models import ApiErrors
from pcapi.models import VenueProvider
from pcapi.repository import repository
from pcapi.use_cases.connect_venue_to_provider import connect_venue_to_provider


class WhenProviderIsLibraires:
    def setup_class(self):
        self.find_by_id = MagicMock()

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.api_libraires_stocks.can_be_synchronized",
        return_value=True,
    )
    def should_connect_venue_when_synchronization_is_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        provider = activate_provider("LibrairesStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = True

        # When
        connect_venue_to_provider(venue, provider)

        # Then
        libraires_venue_provider = VenueProvider.query.one()
        assert libraires_venue_provider.venue == venue

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.api_libraires_stocks.can_be_synchronized",
        return_value=False,
    )
    def should_not_connect_venue_when_synchronization_is_not_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret="12345678912345")
        provider = activate_provider("LibrairesStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = False

        # when
        with pytest.raises(ApiErrors) as error:
            print(connect_venue_to_provider(venue, provider))

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec Leslibraires.fr n’est pas disponible pour le SIRET 12345678912345"
        ]

    @pytest.mark.usefixtures("db_session")
    def should_not_connect_venue_when_venue_has_no_siret(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret=None, is_virtual=True)
        provider = activate_provider("LibrairesStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec Leslibraires.fr n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres."
        ]


class WhenProviderIsTiteLive:
    def setup_class(self):
        self.find_by_id = MagicMock()

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.api_titelive_stocks.can_be_synchronized",
        return_value=True,
    )
    def should_connect_venue_when_synchronization_is_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        provider = activate_provider("TiteLiveStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = True

        # When
        connect_venue_to_provider(venue, provider)

        # Then
        titelive_venue_provider = VenueProvider.query.one()
        assert titelive_venue_provider.venue == venue

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.api_titelive_stocks.can_be_synchronized",
        return_value=False,
    )
    def should_not_connect_venue_when_synchronization_is_not_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret="12345678912345")
        provider = activate_provider("TiteLiveStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = False

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec TiteLive Stocks (Epagine / Place des libraires.com) n’est pas disponible pour le SIRET 12345678912345"
        ]

    @pytest.mark.usefixtures("db_session")
    def should_not_connect_venue_when_venue_has_no_siret(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret=None, is_virtual=True)
        provider = activate_provider("TiteLiveStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = True

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec TiteLive Stocks (Epagine / Place des libraires.com) n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres."
        ]


class WhenProviderImplementsProviderAPI:
    def setup_class(self):
        self.find_by_id = MagicMock()

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.synchronize_provider_api.check_siret_can_be_synchronized",
        return_value=True,
    )
    def should_connect_venue_when_synchronization_is_allowed(self, app):
        # Given
        offerer = create_offerer()

        venue = create_venue(offerer)
        provider = offerers_factories.APIProviderFactory()

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = True

        # When
        connect_venue_to_provider(venue, provider)

        # Then
        fnac_venue_provider = VenueProvider.query.one()
        assert fnac_venue_provider.venue == venue

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.synchronize_provider_api.check_siret_can_be_synchronized",
        return_value=False,
    )
    def should_not_connect_venue_when_synchronization_is_not_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret="12345678912345")
        provider = offerers_factories.APIProviderFactory(name="FNAC")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = False

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec FNAC n’est pas disponible pour le SIRET 12345678912345"
        ]

    @pytest.mark.usefixtures("db_session")
    def should_not_connect_venue_when_venue_has_no_siret(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret=None, is_virtual=True)
        provider = offerers_factories.APIProviderFactory(name="FNAC")

        repository.save(venue)

        self.find_by_id.return_value = venue

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec FNAC n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres."
        ]


class WhenProviderIsPraxiel:
    def setup_class(self):
        self.find_by_id = MagicMock()

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.api_praxiel_stocks.can_be_synchronized",
        return_value=True,
    )
    def should_connect_venue_when_synchronization_is_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        provider = activate_provider("PraxielStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = True

        # When
        connect_venue_to_provider(venue, provider)

        # Then
        praxiel_venue_provider = VenueProvider.query.one()
        assert praxiel_venue_provider.venue == venue

    @pytest.mark.usefixtures("db_session")
    @patch(
        "pcapi.use_cases.connect_venue_to_provider.api_praxiel_stocks.can_be_synchronized",
        return_value=False,
    )
    def should_not_connect_venue_when_synchronization_is_not_allowed(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret="12345678912345")
        provider = activate_provider("PraxielStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue
        stock_repository = MagicMock()
        stock_repository.can_be_synchronized.return_value = False

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec Praxiel/Inférence n’est pas disponible pour le SIRET 12345678912345"
        ]

    @pytest.mark.usefixtures("db_session")
    def should_not_connect_venue_when_venue_has_no_siret(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret=None, is_virtual=True)
        provider = activate_provider("PraxielStocks")

        repository.save(venue)

        self.find_by_id.return_value = venue

        # when
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # then
        assert error.value.errors["provider"] == [
            "L’importation d’offres avec Praxiel/Inférence n’est pas disponible sans SIRET associé au lieu. Ajoutez un SIRET pour pouvoir importer les offres."
        ]


class WhenProviderIsSomethingElse:
    def setup_class(self):
        self.find_by_id = MagicMock()

    @pytest.mark.usefixtures("db_session")
    def should_raise_an_error(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        provider = create_provider(local_class="TestLocalProvider")
        repository.save(venue, provider)

        self.find_by_id.return_value = venue

        # When
        with pytest.raises(ApiErrors) as error:
            connect_venue_to_provider(venue, provider)

        # Then
        assert error.value.errors["provider"] == ["Provider non pris en charge"]
