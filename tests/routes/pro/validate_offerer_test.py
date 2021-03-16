import secrets
from unittest.mock import call
from unittest.mock import patch

import pytest

from pcapi.core.offerers.models import Offerer
from pcapi.core.testing import override_features
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.model_creators.generic_creators import create_venue
from pcapi.repository import repository

from tests.conftest import TestClient


class Get:
    class Returns202:
        @pytest.mark.usefixtures("db_session")
        def expect_offerer_to_be_validated(self, app):
            # Given
            offerer_token = secrets.token_urlsafe(20)
            offerer = create_offerer(validation_token=offerer_token)
            user = create_user()
            admin = create_user_offerer(user, offerer)
            repository.save(admin)

            # When
            response = TestClient(app.test_client()).get(
                f"/validate/offerer/{offerer_token}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 202
            offerer = Offerer.query.filter_by(id=offerer.id).first()
            assert offerer.isValidated is True

        @patch("pcapi.routes.pro.validate.link_valid_venue_to_irises")
        @pytest.mark.usefixtures("db_session")
        def expect_link_venue_to_iris_if_valid_to_have_been_called_for_every_venue(
            self, mocked_link_venue_to_iris_if_valid, app
        ):
            # Given
            offerer_token = secrets.token_urlsafe(20)
            offerer = create_offerer(validation_token=offerer_token)
            create_venue(offerer)
            create_venue(offerer, siret=f"{offerer.siren}65371")
            create_venue(offerer, is_virtual=True, siret=None)
            user = create_user()
            admin = create_user_offerer(user, offerer)
            repository.save(admin)

            # When
            response = TestClient(app.test_client()).get(
                f"/validate/offerer/{offerer_token}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 202
            assert mocked_link_venue_to_iris_if_valid.call_count == 3

        @patch("pcapi.routes.pro.validate.redis.add_venue_id")
        @pytest.mark.usefixtures("db_session")
        def expect_offerer_managed_venues_to_be_added_to_redis_when_feature_is_active(self, mocked_redis, app):
            # Given
            offerer_token = secrets.token_urlsafe(20)
            offerer = create_offerer(validation_token=offerer_token)
            create_venue(offerer, idx=1)
            create_venue(offerer, idx=2, siret=f"{offerer.siren}65371")
            create_venue(offerer, idx=3, is_virtual=True, siret=None)
            user = create_user()
            admin = create_user_offerer(user, offerer)
            repository.save(admin)

            # When
            response = TestClient(app.test_client()).get(
                f"/validate/offerer/{offerer_token}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 202
            assert mocked_redis.call_count == 3
            assert mocked_redis.call_args_list == [
                call(client=app.redis_client, venue_id=1),
                call(client=app.redis_client, venue_id=2),
                call(client=app.redis_client, venue_id=3),
            ]

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.validate.redis.add_venue_id")
        @override_features(SYNCHRONIZE_ALGOLIA=False)
        def expect_offerer_managed_venues_not_to_be_added_to_redis_when_feature_is_not_active(self, mocked_redis, app):
            # Given
            offerer_token = secrets.token_urlsafe(20)
            offerer = create_offerer(validation_token=offerer_token)
            create_venue(offerer)
            create_venue(offerer, siret=f"{offerer.siren}65371")
            create_venue(offerer, is_virtual=True, siret=None)
            user = create_user()
            admin = create_user_offerer(user, offerer)
            repository.save(admin)

            # When
            response = TestClient(app.test_client()).get(
                f"/validate/offerer/{offerer_token}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 202
            assert mocked_redis.call_count == 0

    class Returns404:
        @pytest.mark.usefixtures("db_session")
        def expect_offerer_not_to_be_validated_with_unknown_token(self, app):
            # When
            response = TestClient(app.test_client()).with_auth(email="pro@example.com").get("/validate/offerer/123")

            # Then
            assert response.status_code == 404
