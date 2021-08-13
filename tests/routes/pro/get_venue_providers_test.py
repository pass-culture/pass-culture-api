import datetime

import pytest
import pytz

from pcapi.core.offerers import factories as offerers_factories
from pcapi.core.providers.repository import get_provider_by_local_class
from pcapi.core.users import factories as users_factories
from pcapi.utils.date import CUSTOM_TIMEZONES
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


class Returns200Test:
    @pytest.mark.usefixtures("db_session")
    def test_get_list_with_valid_venue_id(self, app):
        # given
        user = users_factories.ProFactory()
        titelive_things_provider = get_provider_by_local_class("TiteLiveThings")
        venue_provider = offerers_factories.VenueProviderFactory(
            venue__name="Librairie Titelive",
            provider=titelive_things_provider,
        )

        # when
        auth_request = TestClient(app.test_client()).with_auth(email=user.email)
        response = auth_request.get("/venueProviders?venueId=" + humanize(venue_provider.venue.id))

        # then
        assert response.status_code == 200
        assert response.json["venue_providers"][0].get("id") == humanize(venue_provider.id)
        assert response.json["venue_providers"][0].get("venueId") == humanize(venue_provider.venue.id)

    @pytest.mark.usefixtures("db_session")
    def test_get_list_that_include_allocine_with_valid_venue_id(self, app):
        # given
        user = users_factories.ProFactory()
        allocine_stocks_provider = get_provider_by_local_class("AllocineStocks")
        allocine_venue_provider = offerers_factories.AllocineVenueProviderFactory(
            venue__name="Whatever cinema",
            provider=allocine_stocks_provider,
        )

        # when
        auth_request = TestClient(app.test_client()).with_auth(email=user.email)
        response = auth_request.get("/venueProviders?venueId=" + humanize(allocine_venue_provider.venue.id))

        # then
        assert response.status_code == 200
        assert response.json["venue_providers"][0].get("id") == humanize(allocine_venue_provider.id)
        assert response.json["venue_providers"][0].get("venueId") == humanize(allocine_venue_provider.venue.id)

    @pytest.mark.usefixtures("db_session")
    @pytest.mark.parametrize("department_code, timezone", [(46, "Europe/Paris")] + list(CUSTOM_TIMEZONES.items()))
    @pytest.mark.parametrize(
        "provider_class, provider_factory",
        [
            ("AllocineStocks", offerers_factories.AllocineVenueProviderFactory),
            ("TiteLiveThings", offerers_factories.VenueProviderFactory),
        ],
    )
    def test_provider_last_sync_date_timezone_according_to_venue_department(
        self, app, department_code, timezone, provider_class, provider_factory
    ):
        # given
        naive_now = datetime.datetime.now()
        utc_now = pytz.timezone("UTC").localize(naive_now)
        homeland_now = utc_now.astimezone(pytz.timezone(timezone))
        user = users_factories.ProFactory()
        provider = get_provider_by_local_class(provider_class)
        venue_provider = provider_factory(
            venue__departementCode=department_code, provider=provider, lastSyncDate=utc_now
        )

        # when
        auth_request = TestClient(app.test_client()).with_auth(email=user.email)
        response = auth_request.get("/venueProviders?venueId={}".format(humanize(venue_provider.venue.id)))

        # then
        response_last_sync_date = datetime.datetime.strptime(
            response.json["venue_providers"][0]["lastSyncDate"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        assert response_last_sync_date == homeland_now


class Returns400Test:
    @pytest.mark.usefixtures("db_session")
    def when_listing_all_venues_without_venue_id_argument(self, app):
        # given
        user = users_factories.ProFactory()
        titelive_things_provider = get_provider_by_local_class("TiteLiveThings")
        offerers_factories.VenueProviderFactory(
            venue__name="Librairie Titelive",
            provider=titelive_things_provider,
        )

        # when
        auth_request = TestClient(app.test_client()).with_auth(email=user.email)
        response = auth_request.get("/venueProviders")

        # then
        assert response.status_code == 400
