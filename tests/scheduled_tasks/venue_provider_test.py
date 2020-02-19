from unittest.mock import MagicMock, patch

from scheduled_tasks.venue_provider import synchronize_libraires_stocks


class FakeProvider(object):
    pass


class SynchronizeLibrairesStocksTest:
    @patch('scheduled_tasks.decorators.feature_queries.is_active')
    @patch('scheduled_tasks.venue_provider.get_provider_by_local_class')
    @patch('scheduled_tasks.venue_provider.synchronize_venue_providers_for_provider')
    def test_should_call_synchronize_with_provider_id_when_feature_is_active(self, mock_synchronize,
                                                                             mock_get_provider_by_local_class,
                                                                             mock_feature_is_active):
        # Given
        app_fixture = MagicMock()
        app_fixture.app_context = MagicMock()
        provider = FakeProvider()
        provider.id = 4
        mock_get_provider_by_local_class.return_value = provider
        mock_feature_is_active.return_value = True

        # When
        synchronize_libraires_stocks(app_fixture)

        # Then
        mock_get_provider_by_local_class.assert_called_once_with("LibrairesStocks")
        mock_synchronize.assert_called_once_with(4)

    @patch('scheduled_tasks.decorators.feature_queries.is_active')
    @patch('scheduled_tasks.venue_provider.get_provider_by_local_class')
    @patch('scheduled_tasks.venue_provider.synchronize_venue_providers_for_provider')
    def test_should_not_call_synchronize_when_feature_is_not_active(self, mock_synchronize,
                                                                    mock_get_provider_by_local_class,
                                                                    mock_feature_is_active):
        # Given
        app_fixture = MagicMock()
        app_fixture.app_context = MagicMock()
        provider = FakeProvider()
        provider.id = 4
        mock_get_provider_by_local_class.return_value = provider
        mock_feature_is_active.return_value = False

        # When
        synchronize_libraires_stocks(app_fixture)

        # Then
        mock_get_provider_by_local_class.assert_not_called()
        mock_synchronize.assert_not_called()
