import pytest

from pcapi.model_creators.generic_creators import create_mediation
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.models import FavoriteSQLEntity
from pcapi.repository import repository
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


class Post:
    class Returns400:
        @pytest.mark.usefixtures("db_session")
        def when_offer_id_is_not_received(self, app):
            # Given
            user = create_user(email="test@email.com")
            repository.save(user)

            json = {
                "mediationId": "DA",
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post("/favorites", json=json)

            # Then
            assert response.status_code == 400
            assert response.json["global"] == ["Le paramètre offerId est obligatoire"]

    class Returns404:
        @pytest.mark.usefixtures("db_session")
        def when_offer_is_not_found(self, app):
            # Given
            user = create_user(email="test@email.com")
            offerer = create_offerer()
            venue = create_venue(offerer, postal_code="29100", siret="12345678912341")
            offer = create_offer_with_thing_product(venue, thumb_count=0)
            mediation = create_mediation(offer, is_active=True)
            repository.save(user)

            json = {
                "offerId": "ABCD",
                "mediationId": humanize(mediation.id),
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post("/favorites", json=json)

            # Then
            assert response.status_code == 404

        @pytest.mark.usefixtures("db_session")
        def when_mediation_is_not_found(self, app):
            # Given
            user = create_user(email="test@email.com")
            offerer = create_offerer()
            venue = create_venue(offerer, postal_code="29100", siret="12345678912341")
            offer = create_offer_with_thing_product(venue, thumb_count=0)
            mediation = create_mediation(offer, is_active=True)
            repository.save(user, mediation)

            json = {
                "offerId": humanize(offer.id),
                "mediationId": "ABCD",
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post("/favorites", json=json)

            # Then
            assert response.status_code == 404

    class Returns201:
        @pytest.mark.usefixtures("db_session")
        def when_offer_is_added_as_favorite_for_current_user(self, app):
            # Given
            user = create_user(email="test@email.com")
            offerer = create_offerer()
            venue = create_venue(offerer, postal_code="29100", siret="12345678912341")
            offer = create_offer_with_thing_product(venue, thumb_count=0)
            mediation = create_mediation(offer, is_active=True)
            repository.save(user, mediation)

            json = {
                "offerId": humanize(offer.id),
                "mediationId": humanize(mediation.id),
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post("/favorites", json=json)

            # Then
            assert response.status_code == 201

            favorite = FavoriteSQLEntity.query.one()
            assert favorite.offerId == offer.id
            assert favorite.mediationId == mediation.id
            assert favorite.userId == user.id

        @pytest.mark.usefixtures("db_session")
        def when_mediation_id_doest_not_exist(self, app):
            # Given
            user = create_user(email="test@email.com")
            offerer = create_offerer()
            venue = create_venue(offerer, postal_code="29100", siret="12345678912341")
            offer = create_offer_with_thing_product(venue, thumb_count=0)
            repository.save(user, offer)

            json = {
                "offerId": humanize(offer.id),
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post("/favorites", json=json)

            # Then
            assert response.status_code == 201
