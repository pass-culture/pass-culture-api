from unittest.mock import MagicMock
from unittest.mock import patch

from pcapi.models import ApiErrors
from pcapi.workers.mailing_contacts_job import mailing_contacts_job

from tests.conftest import TestClient


class Post:
    class Returns201:
        @patch("pcapi.routes.webapp.mailing_contacts.validate_save_mailing_contact_request")
        def when_contact_has_successfully_been_saved(self, validate_request, app):
            # Given
            mailing_contacts_job.delay = MagicMock()
            data = {"email": "jeune@example.com", "dateOfBirth": "2003-02-02"}

            # When
            response = TestClient(app.test_client()).post("/mailing-contacts", json=data)

            # Then
            mailing_contacts_job.delay.assert_called_once_with(
                data["email"], data["dateOfBirth"]
            )
            validate_request.assert_called_once_with(data)
            assert response.status_code == 201

    class Returns400:
        @patch("pcapi.routes.webapp.mailing_contacts.validate_save_mailing_contact_request")
        def when_payload_validation_fails(self, validate_request, app):
            # Given
            data = {"dateOfBirth": "2003-02-02"}

            validate_request.side_effect = ApiErrors({"email": "L'email est manquant"})

            # When
            response = TestClient(app.test_client()).post("/mailing-contacts", json=data)

            # Then
            validate_request.assert_called_once_with(data)
            assert response.status_code == 400
