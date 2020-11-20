from unittest.mock import patch

import pytest

from pcapi.workers.bank_information_job import bank_information_job

from tests.conftest import TestClient


class Post:
    class Returns202:
        @patch("pcapi.routes.bank_informations.bank_information_job.delay")
        @patch("pcapi.settings.DEMARCHES_SIMPLIFIEES_WEBHOOK_TOKEN", "good_token")
        @pytest.mark.usefixtures("db_session")
        def when_has_valid_provider_name_and_dossier_id(self, mock_bank_information_job, app):
            # Given
            data = {"dossier_id": "666"}

            # When
            response = TestClient(app.test_client()).post(
                "/bank_informations/venue/application_update?token=good_token", form=data
            )

            # Then
            assert response.status_code == 202
            mock_bank_information_job.assert_called_once_with("666", "venue")

    class Returns400:
        @patch("pcapi.routes.bank_informations.bank_information_job.delay")
        @patch("pcapi.settings.DEMARCHES_SIMPLIFIEES_WEBHOOK_TOKEN", "good_token")
        @pytest.mark.usefixtures("db_session")
        def when_has_not_dossier_in_request_form_data(self, mock_bank_information_job, app):
            # Given
            data = {"fake_key": "666"}

            # When
            response = TestClient(app.test_client()).post(
                "/bank_informations/venue/application_update?token=good_token", form=data
            )

            # Then
            assert response.status_code == 400

    class Returns403:
        @patch("pcapi.routes.bank_informations.bank_information_job.delay")
        @patch("pcapi.settings.DEMARCHES_SIMPLIFIEES_WEBHOOK_TOKEN", "good_token")
        @pytest.mark.usefixtures("db_session")
        def when_has_not_a_token_in_url_params(self, mock_bank_information_job, app):
            # Given
            data = {"dossier_id": "666"}

            # When
            response = TestClient(app.test_client()).post("/bank_informations/venue/application_update", form=data)

            # Then
            assert response.status_code == 403

        @patch("pcapi.routes.bank_informations.bank_information_job.delay")
        @patch("pcapi.settings.DEMARCHES_SIMPLIFIEES_WEBHOOK_TOKEN", "good_token")
        @pytest.mark.usefixtures("db_session")
        def when_token_in_url_params_is_not_good(self, mock_bank_information_job, app):
            # Given
            data = {"dossier_id": "666"}

            # When
            response = TestClient(app.test_client()).post(
                "/bank_informations/venue/application_update?token=ABCD", form=data
            )

            # Then
            assert response.status_code == 403
