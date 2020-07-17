from unittest.mock import patch, MagicMock

import pytest

from connectors.api_matomo import run_matomo_archiving, MatomoException


class RunMatomoArchivingTest:
    @patch('connectors.api_matomo.requests.get')
    def test_should_call_matomo_server(self, request_get):
        # Given
        matomo_auth_token = 'XYZ'
        matomo_server_url = 'http://matomo.app'
        expected_result = {'toto'}
        response_return_value = MagicMock(status_code=200, text='')
        response_return_value.json = MagicMock(return_value=expected_result)
        request_get.return_value = response_return_value

        # When
        run_matomo_archiving(matomo_server_url, matomo_auth_token)

        # Then
        request_get.assert_called_once_with(f"http://matomo.app/misc/cron/archive.php?token_auth=XYZ")

    @patch('connectors.api_matomo.requests.get', side_effect=Exception)
    def test_should_raise_exception_when_api_call_fails(self, request_get):
        # Given
        matomo_auth_token = 'XYZ'
        matomo_server_url = 'http://matomo.app'
        expected_result = {'toto'}
        response_return_value = MagicMock(status_code=200, text='')
        response_return_value.json = MagicMock(return_value=expected_result)
        request_get.return_value = response_return_value

        # When
        with pytest.raises(MatomoException) as exception:
            run_matomo_archiving(matomo_server_url, matomo_auth_token)

        # Then
        assert str(exception.value) == "Error connecting Matomo Server"

    @patch('connectors.api_matomo.requests.get')
    def test_should_raise_exception_when_api_call_fails_with_connection_error(self, request_get):
        # Given
        matomo_auth_token = 'XYZ'
        matomo_server_url = 'http://matomo.app'
        expected_result = {'toto'}
        response_return_value = MagicMock(status_code=404, text='')
        response_return_value.json = MagicMock(return_value=expected_result)
        request_get.return_value = response_return_value

        # When
        with pytest.raises(MatomoException) as matomo_exception:
            run_matomo_archiving(matomo_server_url, matomo_auth_token)

        # Then
        assert str(matomo_exception.value) == "Error getting API Matomo; Respond with statut code : 404"
