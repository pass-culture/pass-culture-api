from unittest.mock import patch
import pytest
from sqlalchemy_api_handler import ApiErrors, ApiHandler, humanize

from tests.conftest import clean_database, TestClient
from tests.test_utils import create_offerer, create_venue, create_user, activate_provider, \
    check_titelive_stocks_api_is_down, create_product_with_thing_type


class Post:
    class Returns201:
        @clean_database
        @pytest.mark.skipif(check_titelive_stocks_api_is_down(), reason="TiteLiveStocks API is down")
        def when_venue_provider_exists(self, app):
            # given
            offerer = create_offerer(siren='775671464')
            venue = create_venue(offerer, name='Librairie Titelive', siret='77567146400110')
            ApiHandler.save(venue)

            provider = activate_provider('TiteLiveStocks')
            product = create_product_with_thing_type(id_at_providers='0002730757438')

            venue_provider_data = {'providerId': humanize(provider.id),
                                   'venueId': humanize(venue.id),
                                   'venueIdAtOfferProvider': '77567146400110'}
            user = create_user(is_admin=True, can_book_free_offers=False)
            ApiHandler.save(product, user)
            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            # when
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # then
            assert response.status_code == 201

            json_response = response.json
            assert 'id' in json_response
            venue_provider_id = json_response['id']
            assert json_response['lastSyncDate'] is None

    class Returns400:
        @clean_database
        @patch('routes.venue_providers.validate_new_venue_provider_information')
        def when_api_error_raise_from_payload_validation(self, validate_new_venue_provider_information, app):
            # given
            api_errors = ApiErrors()
            api_errors.status_code = 400
            api_errors.add_error('errors', 'error received')

            validate_new_venue_provider_information.side_effect = api_errors

            user = create_user(is_admin=True, can_book_free_offers=False)
            ApiHandler.save(user)
            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)
            venue_provider_data = {
                'providerId': 'B9',
                'venueId': 'B9',
                'venueIdAtOfferProvider': '77567146400110'
            }

            # when
            response = auth_request.post('/venueProviders', json=venue_provider_data)

            # then
            assert response.status_code == 400
            assert ['error received'] == response.json['errors']
