from unittest.mock import patch

import pytest

from pcapi.core.testing import override_features
from pcapi.model_creators.generic_creators import create_allocine_pivot
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.generic_creators import create_venue_provider
from pcapi.model_creators.provider_creators import activate_provider
from pcapi.models import ApiErrors
from pcapi.models import VenueProvider
from pcapi.repository import repository
from pcapi.utils.human_ids import dehumanize
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient
from tests.conftest import clean_database


class Post:
    class Returns201:
        @pytest.mark.usefixtures("db_session")
        @override_features(SYNCHRONIZE_VENUE_PROVIDER_IN_WORKER=False)
        @patch("pcapi.routes.pro.venue_providers.subprocess.Popen")
        @patch("pcapi.use_cases.connect_venue_to_provider._check_venue_can_be_synchronized_with_provider")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_venue_provider_is_successfully_created_and_using_subprocesses(
            self, stubbed_find_by_id, stubbed_check, mock_subprocess, app
        ):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret="12345678912345")
            repository.save(venue, user)

            stubbed_find_by_id.return_value = venue

            provider = activate_provider("LibrairesStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 201
            venue_provider = VenueProvider.query.one()
            assert venue_provider.venueId == venue.id
            assert venue_provider.providerId == provider.id
            assert venue_provider.venueIdAtOfferProvider == "12345678912345"
            assert "id" in response.json
            venue_provider_id = response.json["id"]
            mock_subprocess.assert_called_once_with(
                [
                    "python",
                    "src/pcapi/scripts/pc.py",
                    "update_providables",
                    "--venue-provider-id",
                    str(dehumanize(venue_provider_id)),
                ]
            )

        @pytest.mark.usefixtures("db_session")
        @override_features(SYNCHRONIZE_VENUE_PROVIDER_IN_WORKER=True)
        @patch("pcapi.workers.venue_provider_job.venue_provider_job.delay")
        @patch("pcapi.use_cases.connect_venue_to_provider._check_venue_can_be_synchronized_with_provider")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_venue_provider_is_successfully_created(
            self, stubbed_find_by_id, stubbed_check, mock_synchronize_venue_provider, app
        ):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret="12345678912345")
            repository.save(venue, user)

            stubbed_find_by_id.return_value = venue

            provider = activate_provider("LibrairesStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 201
            venue_provider = VenueProvider.query.one()
            assert venue_provider.venueId == venue.id
            assert venue_provider.providerId == provider.id
            assert venue_provider.venueIdAtOfferProvider == "12345678912345"
            assert "id" in response.json
            venue_provider_id = response.json["id"]
            mock_synchronize_venue_provider.assert_called_once_with(dehumanize(venue_provider_id))

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        @patch("pcapi.use_cases.connect_venue_to_allocine.get_allocine_theaterId_for_venue")
        def when_add_allocine_stocks_provider_with_price_but_no_isDuo_config(
            self, stubbed_get_theaterid_for_venue, stubbed_find_by_id, app
        ):
            # Given
            offerer = create_offerer(siren="775671464")
            venue = create_venue(offerer)
            user = create_user(is_admin=True, is_beneficiary=False)
            allocine_pivot = create_allocine_pivot(siret=venue.siret)
            repository.save(venue, user, allocine_pivot)
            stubbed_find_by_id.return_value = venue
            stubbed_get_theaterid_for_venue.return_value = allocine_pivot.theaterId

            provider = activate_provider("AllocineStocks")

            venue_provider_data = {"providerId": humanize(provider.id), "venueId": humanize(venue.id), "price": "9.99"}

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 201
            json = response.json
            assert "_sa_polymorphic_on" not in json
            venue_provider = VenueProvider.query.one()
            assert json["venueId"] == humanize(venue_provider.venueId)

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_add_allocine_stocks_provider_with_default_settings_at_import(self, stubbed_find_by_id, app):
            # Given
            offerer = create_offerer(siren="775671464")
            venue = create_venue(offerer)
            user = create_user(is_admin=True, is_beneficiary=False)
            repository.save(venue, user)
            stubbed_find_by_id.return_value = venue

            provider = activate_provider("AllocineStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
                "price": "9.99",
                "available": 50,
                "isDuo": True,
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 201

    class Returns400:
        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.venue_providers.check_new_venue_provider_information")
        def when_api_error_raise_from_payload_validation(self, mock_check_new_venue_provider_information, app):
            # Given
            api_errors = ApiErrors()
            api_errors.status_code = 400
            api_errors.add_error("errors", "error received")

            mock_check_new_venue_provider_information.side_effect = api_errors

            user = create_user(is_beneficiary=False, is_admin=True)
            repository.save(user)
            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            venue_provider_data = {
                "providerId": "B9",
                "venueId": "B9",
            }

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert ["error received"] == response.json["errors"]

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.use_cases.connect_venue_to_provider._check_venue_can_be_synchronized_with_provider")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_trying_to_add_existing_provider(self, stubbed_find_by_id, stubbed_check, app):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret="12345678912345")
            provider = activate_provider("LibrairesStocks")
            venue_provider = create_venue_provider(venue, provider, venue_id_at_offer_provider="12345678912345")
            repository.save(user, venue_provider)
            stubbed_find_by_id.return_value = venue

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }
            stubbed_check.return_value = True

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert response.json["global"] == ["Votre lieu est déjà lié à cette source"]

        @clean_database
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_add_allocine_stocks_provider_with_wrong_format_price(self, stubbed_find_by_id, app):
            # Given
            offerer = create_offerer(siren="775671464")
            venue = create_venue(offerer)
            user = create_user(is_admin=True, is_beneficiary=False)
            repository.save(venue, user)
            stubbed_find_by_id.return_value = venue

            provider = activate_provider("AllocineStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
                "price": "wrong_price",
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert response.json["global"] == ["Le prix doit être un nombre décimal"]
            assert VenueProvider.query.count() == 0

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_add_allocine_stocks_provider_with_no_price(self, stubbed_find_by_id, app):
            # Given
            offerer = create_offerer(siren="775671464")
            venue = create_venue(offerer)
            user = create_user(is_admin=True, is_beneficiary=False)
            repository.save(venue, user)
            stubbed_find_by_id.return_value = venue

            provider = activate_provider("AllocineStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 400
            assert response.json["price"] == ["Cette information est obligatoire"]
            assert VenueProvider.query.count() == 0

    class Returns401:
        @pytest.mark.usefixtures("db_session")
        def when_user_is_not_logged_in(self, app):
            # when
            response = TestClient(app.test_client()).post("/venueProviders")

            # then
            assert response.status_code == 401

    class Returns404:
        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_venue_does_not_exist(self, stubbed_find_by_id, app):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer(siren="775671464")
            repository.save(user, offerer)
            stubbed_find_by_id.return_value = None

            provider = activate_provider("LibrairesStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": "AZERT",
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 404

    class Returns422:
        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.use_cases.connect_venue_to_provider._check_venue_can_be_synchronized_with_provider")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        def when_provider_api_not_available(self, stubbed_find_by_id, stubbed_check, app):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret="12345678912345")
            repository.save(venue, user)
            stubbed_find_by_id.return_value = venue

            provider = activate_provider("LibrairesStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)

            errors = ApiErrors()
            errors.status_code = 422
            errors.add_error(
                "provider",
                "L’importation d’offres avec LesLibraires n’est pas disponible " "pour le SIRET 12345678912345",
            )
            stubbed_check.side_effect = [errors]

            # When
            response = auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            assert response.status_code == 422
            assert response.json["provider"] == [
                "L’importation d’offres avec LesLibraires n’est pas disponible pour le SIRET 12345678912345"
            ]
            assert VenueProvider.query.count() == 0

    class ConnectProviderToVenueTest:
        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.use_cases.connect_venue_to_provider._check_venue_can_be_synchronized_with_provider")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        @patch("pcapi.routes.pro.venue_providers.connect_venue_to_provider")
        def should_inject_the_appropriate_repository_to_the_usecase(
            self, mocked_connect_venue_to_provider, stubbed_find_by_id, stubbed_check, app
        ):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret="12345678912345")
            repository.save(venue, user)
            stubbed_find_by_id.return_value = venue

            provider = activate_provider("LibrairesStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            mocked_connect_venue_to_provider.assert_called_once_with(venue, provider)

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.use_cases.connect_venue_to_provider._check_venue_can_be_synchronized_with_provider")
        @patch("pcapi.use_cases.connect_venue_to_allocine.get_allocine_theaterId_for_venue")
        @patch("pcapi.routes.pro.venue_providers.find_by_id")
        @patch("pcapi.routes.pro.venue_providers.connect_venue_to_allocine")
        def should_inject_no_repository_to_the_usecase_when_provider_is_not_concerned(
            self,
            mocked_connect_venue_to_allocine,
            stubbed_find_by_id,
            stubbed_get_theaterId_for_venue,
            stubbed_check,
            app,
        ):
            # Given
            user = create_user(is_admin=True, is_beneficiary=False)
            offerer = create_offerer()
            venue = create_venue(offerer, siret="12345678912345")
            allocine_pivot = create_allocine_pivot(siret=venue.siret)
            repository.save(venue, user)
            stubbed_find_by_id.return_value = venue
            stubbed_get_theaterId_for_venue.return_value = allocine_pivot.theaterId

            provider = activate_provider("AllocineStocks")

            venue_provider_data = {
                "providerId": humanize(provider.id),
                "venueId": humanize(venue.id),
            }

            auth_request = TestClient(app.test_client()).with_auth(email=user.email)
            stubbed_check.return_value = True

            # When
            auth_request.post("/venueProviders", json=venue_provider_data)

            # Then
            mocked_connect_venue_to_allocine.assert_called_once_with(
                venue,
                {"providerId": humanize(provider.id), "venueId": humanize(venue.id)},
            )
