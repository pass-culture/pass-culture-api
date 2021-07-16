import secrets
from unittest.mock import patch

import pytest

from pcapi.core.offerers.models import Offerer
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.model_creators.generic_creators import create_venue
from pcapi.repository import repository

from tests.conftest import TestClient


class Returns202Test:
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

    @patch("pcapi.core.search.async_index_venue_ids")
    @pytest.mark.usefixtures("db_session")
    def expect_offerer_managed_venues_to_be_reindexed(self, mocked_async_index_venue_ids, app):
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
        client = TestClient(app.test_client())
        response = client.get(f"/validate/offerer/{offerer_token}")

        # Then
        assert response.status_code == 202
        mocked_async_index_venue_ids.assert_called_once()
        called_args, _ = mocked_async_index_venue_ids.call_args
        assert set(called_args[0]) == set([1, 2, 3])


class Returns404Test:
    @pytest.mark.usefixtures("db_session")
    def expect_offerer_not_to_be_validated_with_unknown_token(self, app):
        # When
        response = TestClient(app.test_client()).with_auth(email="pro@example.com").get("/validate/offerer/123")

        # Then
        assert response.status_code == 404
