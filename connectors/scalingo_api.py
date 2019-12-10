import os
import requests

from utils.config import API_APPLICATION_NAME

SCALINGO_AUTH_URL = 'https://auth.scalingo.com/v1'
SCALINGO_API_URL = 'https://api.osc-fr1.scalingo.com/v1'


class ScalingoApiException(Exception):
    pass


def _get_application_bearer_token() -> str:
    application_token = os.environ.get('SCALINGO_APP_TOKEN')
    bearer_token_endpoint = '/tokens/exchange'
    api_response = requests.post(f'{SCALINGO_AUTH_URL}{bearer_token_endpoint}',
                                 auth=(None, application_token))
    if api_response.status_code != 200:
        raise ScalingoApiException(f'Error getting bearer token with status {api_response.status_code}:'
                                   f' {api_response.json()}')
    json_response = api_response.json()
    return json_response['token']


def run_process_in_one_off_container(command: str) -> str:
    app_bearer_token = _get_application_bearer_token()
    run_one_off_endpoint = f'/apps/{API_APPLICATION_NAME}/run'
    command_parameters = {
        "command": command,
        "region": "osc-fr1",
        "detached": True,
        "size": "L"
    }
    api_response = requests.post(f'{SCALINGO_API_URL}{run_one_off_endpoint}',
                                 json=command_parameters,
                                 headers={'Authorization': f'Bearer {app_bearer_token}'})
    if api_response.status_code != 200:
        raise ScalingoApiException(f'Error getting bearer token  with status {api_response.status_code}:'
                                   f' {api_response.json()}')
    json_response = api_response.json()
    return json_response["container"]["id"]
