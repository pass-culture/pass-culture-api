import pytest

import pcapi.core.offers.factories as offers_factories
from pcapi.utils.human_ids import humanize


@pytest.mark.usefixtures("db_session")
class DescriptionTest:
    def test_update_venue_description(self, app, client):
        user_offerer = offers_factories.UserOffererFactory()
        venue = offers_factories.VenueFactory(
            managingOfferer=user_offerer.offerer,
        )

        data = {"description": "some random description"}

        client = client.with_auth(user_offerer.user.email)
        venue_id = humanize(venue.id)
        response = client.put(f"/venues/{venue_id}/description", json=data)

        assert response.status_code == 204
        assert venue.description == "some random description"

    def test_update_venue_description_unknown_field(self, app, client):
        user_offerer = offers_factories.UserOffererFactory()
        venue = offers_factories.VenueFactory(
            managingOfferer=user_offerer.offerer,
        )

        data = {"desc": "wrong key"}

        client = client.with_auth(user_offerer.user.email)
        venue_id = humanize(venue.id)
        response = client.put(f"/venues/{venue_id}/description", json=data)

        assert response.status_code == 400
        assert "desc" in response.json

    def test_update_venue_description_too_long(self, app, client):
        user_offerer = offers_factories.UserOffererFactory()
        venue = offers_factories.VenueFactory(
            managingOfferer=user_offerer.offerer,
        )

        data = {"description": "a" * 1024}

        client = client.with_auth(user_offerer.user.email)
        venue_id = humanize(venue.id)
        response = client.put(f"/venues/{venue_id}/description", json=data)

        assert response.status_code == 400
        assert "description" in response.json
