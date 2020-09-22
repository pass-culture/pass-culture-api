from typing import Dict

import requests


class ProviderAPIException(Exception):
    pass


class ProviderAPI:
    def __init__(self, api_url, name):
        self.api_url = api_url
        self.name = name

    def stocks(self, siret: str, last_processed_reference: str = '', modified_since: str = '', limit: int = 1000) -> Dict:
        api_url = self._build_local_provider_url(siret)
        print("URL PROVIDER >>>>>>>>   ", api_url)
        params = self._build_local_provider_params(last_processed_reference, modified_since, limit)

        response = requests.get(api_url, params=params)

        if response.status_code != 200:
            raise ProviderAPIException(
                f'Error {response.status_code} when getting {self.name} stocks for SIRET: {siret}')

        return response.json()

    def is_siret_registered(self, siret: str) -> bool:
        api_url = self._build_local_provider_url(siret)
        response = requests.get(api_url)

        return response.status_code == 200

    def _build_local_provider_url(self, siret: str) -> str:
        return f'{self.api_url}/{siret}'

    def _build_local_provider_params(self, last_processed_isbn: str, modified_since: str, limit: int) -> Dict:
        params = {'limit': str(limit)}

        if last_processed_isbn:
            params['after'] = last_processed_isbn
        if modified_since:
            params['modifiedSince'] = modified_since

        return params
