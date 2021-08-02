import pytest

import pcapi.core.offerers.factories as offerers_factories


pytestmark = pytest.mark.usefixtures("db_session")


class VenuesTest:
    def test_get_venue(self, client):
        venue_type = offerers_factories.VenueTypeFactory()
        venue = offerers_factories.VenueFactory(venueType=venue_type)

        response = client.get(f"/native/v1/venue/{venue.id}")

        assert response.status_code == 200
        assert response.json == {
            "id": venue.id,
            "name": venue.name,
            "latitude": float(venue.latitude),
            "longitude": float(venue.longitude),
            "city": venue.city,
            "publicName": venue.publicName,
            "isVirtual": venue.isVirtual,
            "isPermanent": venue.isPermanent,
            "withdrawalDetails": venue.withdrawalDetails,
            "address": venue.address,
            "postalCode": venue.postalCode,
            "venueTypeEnum": venue.venueType.code,
        }

    def test_get_non_existing_venue(self, client):
        response = client.get("/native/v1/venue/123456789")
        assert response.status_code == 404
