from unittest.mock import MagicMock, patch, ANY

from local_providers.provider_manager import do_update, _remove_worker_id_after_venue_provider_sync_error, \
    synchronize_venue_providers_for_provider, synchronize_data_for_provider
from models import VenueProvider
from repository import repository
from tests.conftest import clean_database
from tests.local_providers.provider_test_utils import TestLocalProvider
from tests.model_creators.generic_creators import create_venue_provider, create_venue, create_offerer, create_provider
from tests.test_utils import fake


def mock_update_objects():
    raise Exception


class DoUpdateTest:
    def test_should_call_provider_objects_synchronization_function(self, app):
        # Given
        provider_mock = MagicMock()
        provider_mock.updateObjects = MagicMock()

        # When
        do_update(provider_mock, 10)

        # Then
        provider_mock.updateObjects.assert_called_once_with(10)

    @patch('local_providers.provider_manager.build_cron_log_message')
    @patch('local_providers.provider_manager._remove_worker_id_after_venue_provider_sync_error')
    def test_should_call_remove_worker_id_when_exception_is_raised(self,
                                                                   mock_remove_worker_id,
                                                                   mock_build_cron_log_message,
                                                                   app):
        # Given
        provider_mock = MagicMock()
        provider_mock.updateObjects = mock_update_objects

        # When
        do_update(provider_mock, 10)

        # Then
        mock_remove_worker_id.assert_called_once_with(provider_mock)
        mock_build_cron_log_message.assert_called_once_with(name='MagicMock',
                                                            status=ANY,
                                                            traceback=ANY)


class RemoveWorkerIdAfterVenueProviderSyncErrorTest:
    @clean_database
    def test_should_not_update_model_when_no_venue_provider_attached_to_provider(self, app):
        # Given
        provider = TestLocalProvider()

        # When
        _remove_worker_id_after_venue_provider_sync_error(provider)

        # Then
        assert VenueProvider.query.count() == 0

    @clean_database
    def test_should_remove_worker_id_value(self, app):
        # Given
        provider_test = create_provider(local_class='TestLocalProvider')
        offerer = create_offerer()
        venue = create_venue(offerer)
        venue_provider = create_venue_provider(venue, provider_test, sync_worker_id='1234567')
        repository.save(venue_provider)

        provider = TestLocalProvider(venue_provider)

        # When
        _remove_worker_id_after_venue_provider_sync_error(provider)

        # Then
        updated_venue_provider = VenueProvider.query.one()
        assert updated_venue_provider.syncWorkerId is None


class SynchronizeVenueProvidersForProviderTest:
    @patch('local_providers.provider_manager.do_update')
    @patch('local_providers.provider_manager.get_local_provider_class_by_name')
    @clean_database
    def test_should_entirely_synchronize_venue_provider(self, mock_get_provider_class, mock_do_update, app):
        # Given
        provider_test = create_provider(local_class='TestLocalProvider')
        offerer = create_offerer()
        venue = create_venue(offerer)
        venue_provider = create_venue_provider(venue, provider_test)
        repository.save(venue_provider)
        mock_get_provider_class.return_value = TestLocalProvider

        # When
        synchronize_venue_providers_for_provider(provider_test.id, None)

        # Then
        mock_get_provider_class.assert_called_once()
        mock_do_update.assert_called_once_with(fake(TestLocalProvider), None)

    @patch('local_providers.provider_manager.do_update')
    @patch('local_providers.provider_manager.get_local_provider_class_by_name')
    @clean_database
    def test_should_synchronize_venue_provider_with_defined_limit(self, mock_get_provider_class, mock_do_update, app):
        # Given
        provider_test = create_provider(local_class='TestLocalProvider')
        offerer = create_offerer()
        venue = create_venue(offerer)
        venue_provider = create_venue_provider(venue, provider_test)
        repository.save(venue_provider)
        mock_get_provider_class.return_value = TestLocalProvider

        # When
        synchronize_venue_providers_for_provider(provider_test.id, 10)

        # Then
        mock_get_provider_class.assert_called_once()
        mock_do_update.assert_called_once_with(fake(TestLocalProvider), 10)


class SynchronizeDataForProviderTest:
    @patch('local_providers.provider_manager.do_update')
    @patch('local_providers.provider_manager.get_local_provider_class_by_name')
    @clean_database
    def test_should_call_do_update_for_specified_provider(self, mock_get_provider_class, mock_do_update, app):
        # Given
        provider_test = create_provider(local_class='TestLocalProvider')
        repository.save(provider_test)
        mock_get_provider_class.return_value = TestLocalProvider

        # When
        synchronize_data_for_provider(provider_test.__class__.__name__, None)

        # Then
        mock_get_provider_class.assert_called_once()
        mock_do_update.assert_called_once_with(fake(TestLocalProvider), None)
