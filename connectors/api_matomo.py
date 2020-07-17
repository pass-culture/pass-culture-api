import requests

class MatomoException(Exception):
    pass

def run_matomo_archiving(matomo_server_url: str, matomo_auth_token: str) -> None:
    api_url = f"{matomo_server_url}/misc/cron/archive.php?token_auth={matomo_auth_token}"

    try:
        api_response = requests.get(api_url)
    except Exception:
        raise MatomoException(f'Error connecting Matomo Server')

    if api_response.status_code != 200:
        raise MatomoException(f'Error getting API Matomo; Respond with statut code : {api_response.status_code}')
