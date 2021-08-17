from unittest.mock import patch

import pytest

from pcapi.core.offerers import api as offerers_api
from pcapi.core.offerers import models as offerers_models
from pcapi.core.offerers.models import ApiKey
import pcapi.core.offers.factories as offers_factories
from pcapi.core.testing import assert_num_queries
from pcapi.models import api_errors
from pcapi.utils.token import random_token


class EditVenueTest:
    @pytest.mark.usefixtures("db_session")
    @patch("pcapi.core.search.async_index_venue_ids")
    def when_changes_on_name_algolia_indexing_is_triggered(self, mocked_async_index_venue_ids):
        # Given
        venue = offers_factories.VenueFactory(
            name="old names",
            publicName="old name",
            city="old City",
        )

        # When
        json_data = {"name": "my new name"}
        offerers_api.update_venue(venue, **json_data)

        # Then
        mocked_async_index_venue_ids.assert_called_once_with([venue.id])

    @pytest.mark.usefixtures("db_session")
    @patch("pcapi.core.search.async_index_venue_ids")
    def when_changes_on_public_name_algolia_indexing_is_triggered(self, mocked_async_index_venue_ids):
        # Given
        venue = offers_factories.VenueFactory(
            name="old names",
            publicName="old name",
            city="old City",
        )

        # When
        json_data = {"publicName": "my new name"}
        offerers_api.update_venue(venue, **json_data)

        # Then
        mocked_async_index_venue_ids.called_once_with([venue.id])

    @pytest.mark.usefixtures("db_session")
    @patch("pcapi.core.search.async_index_venue_ids")
    def when_changes_on_city_algolia_indexing_is_triggered(self, mocked_async_index_venue_ids):
        # Given
        venue = offers_factories.VenueFactory(
            name="old names",
            publicName="old name",
            city="old City",
        )

        # When
        json_data = {"city": "My new city"}
        offerers_api.update_venue(venue, **json_data)

        # Then
        mocked_async_index_venue_ids.assert_called_once_with([venue.id])

    @pytest.mark.usefixtures("db_session")
    @patch("pcapi.core.search.async_index_venue_ids")
    def when_changes_are_not_on_algolia_fields_it_should_not_trigger_indexing(self, mocked_async_index_venue_ids):
        # Given
        venue = offers_factories.VenueFactory(
            name="old names",
            publicName="old name",
            city="old City",
            bookingEmail="old@email.com",
        )

        # When
        json_data = {"bookingEmail": "new@email.com"}
        offerers_api.update_venue(venue, **json_data)

        # Then
        mocked_async_index_venue_ids.assert_not_called()

    @pytest.mark.usefixtures("db_session")
    @patch("pcapi.core.search.async_index_venue_ids")
    def when_changes_in_payload_are_same_as_previous_it_should_not_trigger_indexing(self, mocked_async_index_venue_ids):
        # Given
        venue = offers_factories.VenueFactory(
            name="old names",
            publicName="old name",
            city="old City",
        )

        # When
        json_data = {"city": "old City"}
        offerers_api.update_venue(venue, **json_data)

        # Then
        mocked_async_index_venue_ids.assert_not_called()

    @pytest.mark.usefixtures("db_session")
    def test_empty_siret_is_editable(self, app) -> None:
        # Given
        venue = offers_factories.VenueFactory(
            comment="Pas de siret",
            siret=None,
        )

        venue_data = {
            "siret": venue.managingOfferer.siren + "11111",
        }

        # when
        updated_venue = offerers_api.update_venue(venue, **venue_data)

        # Then
        assert updated_venue.siret == venue_data["siret"]

    @pytest.mark.usefixtures("db_session")
    def test_existing_siret_is_not_editable(self, app) -> None:
        # Given
        venue = offers_factories.VenueFactory()

        # when
        venue_data = {
            "siret": venue.managingOfferer.siren + "54321",
        }
        with pytest.raises(api_errors.ApiErrors) as error:
            offerers_api.update_venue(venue, **venue_data)

        # Then
        assert error.value.errors["siret"] == ["Vous ne pouvez pas modifier le siret d'un lieu"]

    @pytest.mark.usefixtures("db_session")
    def test_latitude_and_longitude_wrong_format(self, app) -> None:
        # given
        venue = offers_factories.VenueFactory(
            isVirtual=False,
        )

        # when
        venue_data = {
            "latitude": -98.82387,
            "longitude": "112°3534",
        }
        with pytest.raises(api_errors.ApiErrors) as error:
            offerers_api.update_venue(venue, **venue_data)

        # Then
        assert error.value.errors["latitude"] == ["La latitude doit être comprise entre -90.0 et +90.0"]
        assert error.value.errors["longitude"] == ["Format incorrect"]

    @pytest.mark.usefixtures("db_session")
    def test_accessibility_fields_are_updated(self, app) -> None:
        # given
        venue = offers_factories.VenueFactory()

        # when
        venue_data = {
            "audioDisabilityCompliant": True,
            "mentalDisabilityCompliant": True,
            "motorDisabilityCompliant": False,
            "visualDisabilityCompliant": False,
        }

        offerers_api.update_venue(venue, **venue_data)

        venue = offerers_models.Venue.query.get(venue.id)
        assert venue.audioDisabilityCompliant
        assert venue.mentalDisabilityCompliant
        assert venue.motorDisabilityCompliant is False
        assert venue.visualDisabilityCompliant is False

    @pytest.mark.usefixtures("db_session")
    def test_no_modifications(self, app) -> None:
        # given
        venue = offers_factories.VenueFactory()

        # when
        venue_data = {
            "departementCode": venue.departementCode,
            "city": venue.city,
            "motorDisabilityCompliant": venue.motorDisabilityCompliant,
        }

        # nothing has changed => nothing to save nor update
        with assert_num_queries(0):
            offerers_api.update_venue(venue, **venue_data)


@pytest.mark.usefixtures("db_session")
class ApiKeyTest:
    def test_generate_and_save_api_key(self):
        offerer = offers_factories.OffererFactory()

        generated_key = offerers_api.generate_and_save_api_key(offerer.id)

        found_api_key = offerers_api.find_api_key(generated_key)

        assert found_api_key.offerer == offerer

    def test_legacy_api_key(self):
        offerer = offers_factories.OffererFactory()
        value = random_token(64)
        ApiKey(value=value, offerer=offerer)

        found_api_key = offerers_api.find_api_key(value)

        assert found_api_key.offerer == offerer

    def test_no_key_found(self):
        assert not offerers_api.find_api_key("legacy-key")
        assert not offerers_api.find_api_key("development_prefix_value")
