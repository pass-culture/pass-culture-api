from unittest.mock import patch

import pytest

from models import SeenOffer
from models.feature import FeatureToggle
from repository import repository
from tests.conftest import clean_database, TestClient
from tests.model_creators.generic_creators import create_offerer, create_venue, create_user
from tests.model_creators.specific_creators import create_offer_with_event_product
from tests.test_utils import deactivate_feature
from utils.human_ids import humanize
from validation.routes.seen_offers import PayloadMissing


class Put:
    class Returns200:
        @clean_database
        def when_user_is_logged_in(self, app):
            # Given
            offerer = create_offerer()
            venue = create_venue(offerer)
            offer = create_offer_with_event_product(venue)
            beneficiary = create_user()
            repository.save(offer, beneficiary)

            auth_request = TestClient(app.test_client()).with_auth(beneficiary.email)

            data = {"offerId": humanize(offer.id),
                    "dateSeen": "2018-12-17T15:59:11.689000Z"}

            # When
            response = auth_request.put('/seen_offers',
                                        json=data)
            # Then
            assert response.status_code == 200
            assert SeenOffer.query.count() == 1

    class Returns400:
        @clean_database
        def when_json_is_not_provided(self, app):
            # Given
            beneficiary = create_user()
            auth_request = TestClient(app.test_client()).with_auth(beneficiary.email)
            repository.save(beneficiary)


            # When
            response = auth_request.put('/seen_offers')

            # Then
            assert response.status_code == 400

        @clean_database
        @patch('routes.seen_offers.check_payload_is_valid')
        def when_json_is_empty(self, check_payload_is_valid_mock, app):
            # Given
            beneficiary = create_user()
            auth_request = TestClient(app.test_client()).with_auth(beneficiary.email)
            repository.save(beneficiary)
            check_payload_is_valid_mock.side_effect = PayloadMissing({'global': 'Données manquantes'})


            # When
            response = auth_request.put('/seen_offers', json={})

            # Then
            assert response.status_code == 400

    class Returns401:
        @clean_database
        def when_user_is_not_logged_in(self, app):
            # When
            response = TestClient(app.test_client()).put('/seen_offers')

            # Then
            assert response.status_code == 401

    class Returns403:
        @clean_database
        def when_feature_is_disabled(self, app):
            # Given
            deactivate_feature(FeatureToggle.SAVE_SEEN_OFFERS)

            # When
            response = TestClient(app.test_client()).put('/seen_offers')

            # Then
            assert response.status_code == 403

