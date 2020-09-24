from unittest.mock import patch

from infrastructure.container import api_libraires_stocks
from local_providers import LibrairesStocks, AllocineStocks
from models import ApiErrors, VenueProvider
from repository import repository
from tests.conftest import TestClient, clean_database
from tests.model_creators.generic_creators import create_offerer, create_user, create_venue, create_venue_provider
from tests.model_creators.provider_creators import activate_provider
from utils.config import API_ROOT_PATH
from utils.human_ids import dehumanize, humanize


class Post:
    class Returns201:
        @clean_database
        @patch('routes.venue_providers.subprocess.Popen')
        @patch('use_cases.connect_provider_to_venue._check_venue_can_be_synchronized_with_provider')
        def when_venue_provider_is_successfully_created(self, stubbed_check, mock_subprocess, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret='12345678912345')
            repository.save(venue, user)

            provider = activate_provider('LibrairesStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 201
            venue_provider = VenueProvider.query.one()
            assert venue_provider.venueId == venue.id
            assert venue_provider.providerId == provider.id
            assert venue_provider.venueIdAtOfferProvider == '12345678912345'
            assert 'id' in response.json
            venue_provider_id = response.json['id']
            mock_subprocess.assert_called_once_with('PYTHONPATH="." python scripts/pc.py update_providables'
                                                    + f' --venue-provider-id {dehumanize(venue_provider_id)}',
                                                    cwd=API_ROOT_PATH,
                                                    shell=True)

        @clean_database
        @patch('routes.venue_providers.subprocess.Popen')
        def when_add_allocine_stocks_provider_with_price_but_no_isDuo_config(self, mock_subprocess, app):
            # Given
            offerer = create_offerer(siren='775671464')
            venue = create_venue(offerer)
            user = create_user(is_admin=True, can_book_free_offers=False)
            repository.save(venue, user)

            provider = activate_provider('AllocineStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
                'price': '9.99'
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 201
            json = response.json
            assert '_sa_polymorphic_on' not in json
            venue_provider = VenueProvider.query.one()
            assert json['venueId'] == humanize(venue_provider.venueId)

        @clean_database
        @patch('routes.venue_providers.subprocess.Popen')
        def when_add_allocine_stocks_provider_with_default_settings_at_import(self, mock_subprocess, app):
            # Given
            offerer = create_offerer(siren='775671464')
            venue = create_venue(offerer)
            user = create_user(is_admin=True, can_book_free_offers=False)
            repository.save(venue, user)

            provider = activate_provider('AllocineStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
                'price': '9.99',
                'available': 50,
                'isDuo': True
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 201

    class Returns400:
        @clean_database
        @patch('routes.venue_providers.check_new_venue_provider_information')
        def when_api_error_raise_from_payload_validation(self, mock_check_new_venue_provider_information, app):
            # Given
            api_errors = ApiErrors()
            api_errors.status_code = 400
            api_errors.add_error('errors', 'error received')

            mock_check_new_venue_provider_information.side_effect = api_errors

            user = create_user(can_book_free_offers=False, is_admin=True)
            repository.save(user)
            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)
            venue_provider_data = {
                'providerId': 'B9',
                'venueId': 'B9',
            }

            # When
            response = auth_request.post('/venueProviders', json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert ['error received'] == response.json['errors']

        @clean_database
        @patch('use_cases.connect_provider_to_venue._check_venue_can_be_synchronized_with_provider')
        def when_trying_to_add_existing_provider(self, stubbed_check, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret='12345678912345')
            provider = activate_provider('LibrairesStocks')
            venue_provider = create_venue_provider(venue, provider, venue_id_at_offer_provider='12345678912345')
            repository.save(user, venue_provider)

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)
            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
            }
            stubbed_check.return_value = True

            # When
            response = auth_request.post('/venueProviders', json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert response.json['global'] == ["Votre lieu est déjà lié à cette source"]

        @clean_database
        @patch('routes.venue_providers.subprocess.Popen')
        def when_add_allocine_stocks_provider_with_wrong_format_price(self, mock_subprocess, app):
            # Given
            offerer = create_offerer(siren='775671464')
            venue = create_venue(offerer)
            user = create_user(is_admin=True, can_book_free_offers=False)
            repository.save(venue, user)

            provider = activate_provider('AllocineStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
                'price': 'wrong_price'
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert response.json['global'] == ["Le prix doit être un nombre décimal"]
            assert VenueProvider.query.count() == 0

        @clean_database
        @patch('routes.venue_providers.subprocess.Popen')
        def when_add_allocine_stocks_provider_with_no_price(self, mock_subprocess, app):
            # Given
            offerer = create_offerer(siren='775671464')
            venue = create_venue(offerer)
            user = create_user(is_admin=True, can_book_free_offers=False)
            repository.save(venue, user)

            provider = activate_provider('AllocineStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert response.json['price'] == ["Cette information est obligatoire"]
            assert VenueProvider.query.count() == 0

    class Returns401:
        @clean_database
        def when_user_is_not_logged_in(self, app):
            # when
            response = TestClient(app.test_client()).post('/venueProviders')

            # then
            assert response.status_code == 401

    class Returns404:
        @clean_database
        def when_venue_does_not_exist(self, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            offerer = create_offerer(siren='775671464')
            venue = create_venue(offerer)
            repository.save(venue, user)

            provider = activate_provider('LibrairesStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': 'AZERT',
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 404

    class Returns422:
        @clean_database
        @patch('use_cases.connect_provider_to_venue._check_venue_can_be_synchronized_with_provider')
        def when_provider_api_not_available(self, stubbed_check, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret='12345678912345')
            repository.save(venue, user)

            provider = activate_provider('LibrairesStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)

            errors = ApiErrors()
            errors.status_code = 422
            errors.add_error('provider', "L’importation d’offres avec LesLibraires n’est pas disponible "
                                         "pour le SIRET 12345678912345")
            stubbed_check.side_effect = [errors]

            # When
            response = auth_request.post('/venueProviders',
                                         json=venue_provider_data)

            # Then
            assert response.status_code == 422
            assert response.json['provider'] == ["L’importation d’offres avec LesLibraires n’est pas disponible "
                                                 "pour le SIRET 12345678912345"]
            assert VenueProvider.query.count() == 0

    class ConnectProviderToVenueTest:
        @clean_database
        @patch('use_cases.connect_provider_to_venue._check_venue_can_be_synchronized_with_provider')
        @patch('routes.venue_providers.connect_provider_to_venue')
        def should_inject_the_appropriate_repository_to_the_usecase(self, stubbed_connect_provider_to_venue,
                                                                    stubbed_check, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret='12345678912345')
            repository.save(venue, user)

            provider = activate_provider('LibrairesStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            auth_request.post('/venueProviders', json=venue_provider_data)

            # Then
            stubbed_connect_provider_to_venue.assert_called_once_with(LibrairesStocks,
                                                                      api_libraires_stocks,
                                                                      {
                                                                          'providerId': humanize(provider.id),
                                                                          'venueId': humanize(venue.id)
                                                                      })

        @clean_database
        @patch('use_cases.connect_provider_to_venue._check_venue_can_be_synchronized_with_provider')
        @patch('routes.venue_providers.connect_provider_to_venue')
        def should_inject_no_repository_to_the_usecase_when_provider_is_not_concerned(self,
                                                                                      stubbed_connect_provider_to_venue,
                                                                                      stubbed_check, app):
            # Given
            user = create_user(is_admin=True, can_book_free_offers=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret='12345678912345')
            repository.save(venue, user)

            provider = activate_provider('AllocineStocks')

            venue_provider_data = {
                'providerId': humanize(provider.id),
                'venueId': humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()) \
                .with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            auth_request.post('/venueProviders', json=venue_provider_data)

            # Then
            stubbed_connect_provider_to_venue.assert_called_once_with(AllocineStocks,
                                                                      None,
                                                                      {
                                                                          'providerId': humanize(provider.id),
                                                                          'venueId': humanize(venue.id)
                                                                      })
