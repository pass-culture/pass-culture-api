from datetime import datetime
from typing import Callable

from connectors.api_libraires import ApiLibrairesStocks, ApiHttpLibrairesStocks


LIBRAIRES_STOCK_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


# domain
class ApiProvider(ABC):
    @abstractmethod
    def get_stock_information(self, siret: str, last_processed_isbn: str = '', modified_since: str = ''):
        pass

    @abstractmethod
    def can_be_synchronized(self, siret: str) -> bool:
        pass


# connectors == repostiories sql
class ApiLibrairesStocks(ApiProvider):
    def __init__(self):
        self.name = 'Libraires'
        self.api_url = API_URL = 'https://passculture.leslibraires.fr/stocks'
        self.api = ApiHttpLibrairesStocks(api_url=API_URL, name='Libraires')

    def get_stock_information(self, siret: str, last_processed_isbn: str = '', modified_since: str = ''):
        result = self.api.get_stocks_from_local_provider_api(siret, ...)
        return result['Stocks']

    def can_be_synchronized_with_libraires(self, siret: str) -> bool:
        return self.api.is_siret_registered(siret)


def get_libraires_stock_information(siret: str, last_processed_isbn: str = '', modified_since: str = '',
                                    get_libraires_stocks: Callable = None) -> iter:
    api_response = get_libraires_stocks(siret, last_processed_isbn, modified_since)
    return iter(api_response['stocks'])


def can_be_synchronized_with_libraires(siret: str) -> bool:
    api = ApiHttpLibrairesStocks(api_url=API_URL, name='Libraires')
    return api.is_siret_registered(siret)


def read_last_modified_date(date: datetime) -> str:
    return datetime.strftime(date, LIBRAIRES_STOCK_DATETIME_FORMAT) if date else ''
