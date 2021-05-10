import pytest

from pcapi.core.offers.factories import VenueLabelFactory
from pcapi.core.users.factories import UserFactory
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


class Get:
    class Returns401:
        @pytest.mark.usefixtures("db_session")
        def when_the_user_is_not_authenticated(self, app):
            # When
            response = TestClient(app.test_client()).get("/venue-labels")

            # then
            assert response.status_code == 401

    class Returns200:
        @pytest.mark.usefixtures("db_session")
        def when_the_user_is_authenticated(self, app):
            # Given
            user = UserFactory(isAdmin=False, isBeneficiary=False)
            venue_label_1 = VenueLabelFactory(label="Maison des illustres")
            venue_label_2 = VenueLabelFactory(label="Monuments historiques")

            # When
            response = TestClient(app.test_client()).with_auth(user.email).get("/venue-labels")

            # then
            assert response.status_code == 200
            assert len(response.json) == 2
            assert response.json == [
                {"id": humanize(venue_label_1.id), "label": venue_label_1.label},
                {"id": humanize(venue_label_2.id), "label": venue_label_2.label},
            ]
