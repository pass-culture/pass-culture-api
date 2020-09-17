from datetime import datetime
from unittest.mock import MagicMock

from infrastructure.repository.stock_provider.provider_api import ProviderAPI
from infrastructure.repository.stock_provider.libraires_stock_provider import StockProviderLibrairesRepository


class StockProviderLibrairesRepositoryTest:
    def setup_method(self):
        ProviderAPI.stocks = MagicMock()
        ProviderAPI.is_siret_registered = MagicMock()
        self.stock_provider_libraires_repository = StockProviderLibrairesRepository()

    def should_call_provider_api_stocks_with_expected_arguments(self):
        # When
        self.stock_provider_libraires_repository.stocks_information(siret='SIRET',
                                                                    last_processed_reference='REF',
                                                                    modified_since=datetime(2019, 10, 1))

        # Then
        ProviderAPI.stocks.assert_called_once_with(siret='SIRET',
                                                   last_processed_ref='REF',
                                                   modified_since='2019-10-01T00:00:00Z')

    def should_call_provider_api_to_know_if_siret_registered_in_provider_api(self):
        # When
        self.stock_provider_libraires_repository.can_be_synchronized(siret='SIRET')

        # Then
        ProviderAPI.is_siret_registered.assert_called_once_with(siret='SIRET')
