from unittest.mock import patch

import pytest

from pcapi.admin.custom_views.venue_provider_view import VenueProviderView
from pcapi.admin.custom_views.venue_view import _get_venue_provider_link
from pcapi.core.offerers.factories import AllocineProviderFactory
from pcapi.core.offerers.factories import ProviderFactory
from pcapi.core.offerers.factories import VenueProviderFactory
from pcapi.core.offers.factories import VenueFactory
from pcapi.core.providers.factories import AllocinePivotFactory
from pcapi.core.providers.models import VenueProvider


class VenueProviderViewTest:
    def test_prevent_access_not_authenticated(self, app, db_session):
        # When
        view = VenueProviderView(VenueProvider, db_session)

        # Then
        assert not view.is_accessible()

    @patch("pcapi.admin.base_configuration.current_user")
    def test_prevent_access_missing_venue_access(self, current_user, app, db_session):
        # Given
        current_user.is_authenticated = True
        current_user.isAdmin = False

        # When
        view = VenueProviderView(VenueProvider, db_session)

        # Then
        assert not view.is_accessible()


class CreateModelTest:
    @patch("pcapi.workers.venue_provider_job.synchronize_venue_provider")
    @patch("pcapi.core.providers.api._siret_can_be_synchronized")
    def test_create_venue_provider(self, mock_siret_can_be_synchronized, synchronize_venue_provider, db_session):
        # Given
        venue = VenueFactory()
        old_provider = ProviderFactory(enabledForPro=True, localClass=None, apiUrl="https://example.com")
        provider = ProviderFactory(enabledForPro=True, localClass=None, apiUrl="https://example.com")
        VenueProviderFactory(provider=old_provider, venue=venue)

        view = VenueProviderView(VenueProvider, db_session)
        VenueProviderForm = view.scaffold_form()
        mock_siret_can_be_synchronized.return_value = True

        data = dict(
            isDuo=None,
            price=None,
            provider=provider,
            venue=venue,
            venueIdAtOfferProvider="hsf4uiagèy12386dq",
        )
        form = VenueProviderForm(data=data)

        # When
        view.create_model(form)

        # Then
        venue_provider = VenueProvider.query.one()
        assert venue_provider.venue == venue
        assert venue_provider.provider == provider
        assert venue_provider.venueIdAtOfferProvider == "hsf4uiagèy12386dq"
        synchronize_venue_provider.assert_called_once_with(venue_provider)

    @patch("pcapi.workers.venue_provider_job.synchronize_venue_provider")
    @patch("pcapi.core.providers.api._siret_can_be_synchronized")
    def test_provider_not_synchronizable(self, mock_siret_can_be_synchronized, synchronize_venue_provider, db_session):
        # Given
        venue = VenueFactory()
        old_provider = ProviderFactory(enabledForPro=True, localClass=None, apiUrl="https://example.com")
        provider = ProviderFactory(enabledForPro=True, localClass=None, apiUrl="https://example.com")
        VenueProviderFactory(provider=old_provider, venue=venue, venueIdAtOfferProvider="old-siret")

        view = VenueProviderView(VenueProvider, db_session)
        VenueProviderForm = view.scaffold_form()
        mock_siret_can_be_synchronized.return_value = False

        data = dict(
            isDuo=None,
            price=None,
            provider=provider,
            venue=venue,
            venueIdAtOfferProvider="hsf4uiagèy12386dq",
        )
        form = VenueProviderForm(data=data)

        # When
        view.create_model(form)

        # Then
        venue_provider = VenueProvider.query.one()
        assert venue_provider.provider == old_provider
        assert venue_provider.venueIdAtOfferProvider == "old-siret"

    @patch("pcapi.workers.venue_provider_job.synchronize_venue_provider")
    def test_create_allocine_provider(self, synchronize_venue_provider, db_session):
        # Give
        venue = VenueFactory(siret="siret-pivot")
        provider = AllocineProviderFactory(enabledForPro=True)
        AllocinePivotFactory(siret="siret-pivot", theaterId="theater-id")

        old_provider = ProviderFactory(localClass=None, apiUrl="https://example.com")
        VenueProviderFactory(provider=old_provider, venue=venue)

        view = VenueProviderView(VenueProvider, db_session)
        VenueProviderForm = view.scaffold_form()

        data = dict(
            isDuo=True,
            price=23.5,
            provider=provider,
            venue=venue,
            venueIdAtOfferProvider=None,
        )
        form = VenueProviderForm(data=data)

        # When
        view.create_model(form)

        # Then
        venue_provider = VenueProvider.query.one()
        assert venue_provider.venue == venue
        assert venue_provider.provider == provider
        assert venue_provider.venueIdAtOfferProvider == "theater-id"
        synchronize_venue_provider.assert_called_once_with(venue_provider)


class GetVenueProviderLinkTest:
    @pytest.mark.usefixtures("db_session")
    def test_return_empty_link_when_no_venue_provider(self, app):
        # Given
        venue = VenueFactory()

        # When
        link = _get_venue_provider_link(None, None, venue, None)

        # Then
        assert not link

    @pytest.mark.usefixtures("db_session")
    def test_return_link_to_venue_provider(self, app):
        # Given
        venue_provider = VenueProviderFactory()
        venue = venue_provider.venue

        # When
        link = _get_venue_provider_link(None, None, venue, None)

        # Then
        assert str(venue.id) in link
        assert "venue_providers" in link
