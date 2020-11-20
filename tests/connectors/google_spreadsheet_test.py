from unittest.mock import patch

import pytest

from pcapi.connectors.google_spreadsheet import MissingGoogleKeyException
from pcapi.connectors.google_spreadsheet import get_credentials


FAKE_GOOGLE_KEY = (
    '{"type": "service_account",'
    '"project_id": "pass-culture", "private_key_id": "1234",'
    '"private_key": "-----BEGIN PRIVATE KEY-----1234'
    '-----END PRIVATE KEY-----",'
    '"client_email": "client@email.com",'
    '"client_id": "4321",'
    '"auth_uri": "https://url.com",'
    '"token_uri": "https://url.com/token",'
    '"auth_provider_x509_cert_url": "https://url.com/certs",'
    '"client_x509_cert_url": "https://url.com/client_x509_cert_url"}'
)


class GetCredentialsTest:
    @patch("pcapi.settings.GOOGLE_KEY", FAKE_GOOGLE_KEY)
    @patch("pcapi.connectors.google_spreadsheet.ServiceAccountCredentials")
    def test_calls_service_account_credentials_from_temp_file_created_from_environ_variable_when_exists(self,
                                                                                                        ServiceAccountCredentials):
        # When
        get_credentials()

        # Then
        ServiceAccountCredentials.from_json_keyfile_name.assert_called_with(
            "/tmp/data.json", ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )

    @patch("pcapi.settings.GOOGLE_KEY", None)
    def test_raises_exception_when_no_environ_variable(self):
        # When / Then
        with pytest.raises(MissingGoogleKeyException):
            get_credentials()

    @patch("pcapi.settings.GOOGLE_KEY", {})
    def test_raises_exception_when_empty_environ_variable(self):
        # When / Then
        with pytest.raises(MissingGoogleKeyException):
            get_credentials()
