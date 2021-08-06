import pytest

import pcapi.core.offers.factories as offers_factories
from pcapi.utils.human_ids import humanize


@pytest.mark.usefixtures("db_session")
class AccessibilityTest:
    def test_update_venue_accessibility(self, app, client):
        user_offerer = offers_factories.UserOffererFactory()
        venue = offers_factories.VenueFactory(
            managingOfferer=user_offerer.offerer,
        )

        data = {
            "audioDisabilityCompliant": True,
            "mentalDisabilityCompliant": True,
            "motorDisabilityCompliant": False,
            "visualDisabilityCompliant": False,
        }

        client = client.with_auth(user_offerer.user.email)
        venue_id = humanize(venue.id)
        response = client.put(f"/venues/{venue_id}/accessibility", json=data)

        assert response.status_code == 204
        assert venue.audioDisabilityCompliant
        assert venue.mentalDisabilityCompliant
        assert venue.motorDisabilityCompliant is False
        assert venue.visualDisabilityCompliant is False

    def test_update_venue_accessibility_errors(self, app, client):
        """
        Ensure that the endpoint applies a strict control over the input
        fields. Meaning:
            extra field -> error
            wrong type -> error
        """
        user_offerer = offers_factories.UserOffererFactory()
        venue = offers_factories.VenueFactory(
            managingOfferer=user_offerer.offerer,
        )

        data = {
            "audioDisabilityCompliant": "should be a boolean",
            "unknown": 0,
        }

        client = client.with_auth(user_offerer.user.email)
        venue_id = humanize(venue.id)
        response = client.put(f"/venues/{venue_id}/accessibility", json=data)

        assert response.status_code == 400
        assert "audioDisabilityCompliant" in response.json
        assert "unknown" in response.json

        assert venue.audioDisabilityCompliant is None
        assert venue.mentalDisabilityCompliant is None
        assert venue.motorDisabilityCompliant is None
        assert venue.visualDisabilityCompliant is None
