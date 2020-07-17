from unittest.mock import patch

from scheduled_tasks.clock import pc_update_recommendations_view, pc_clean_discovery_views, archive_tracking_data


class PcUpdateRecommendationsViewTest:
    @patch('scheduled_tasks.clock.feature_queries.is_active')
    @patch('scheduled_tasks.clock.discovery_view_queries.refresh')
    def test_should_call_refresh_view_when_recommendation_with_geolocation_is_not_active(self,
                                                                                         mock_discovery_refresh,
                                                                                         mock_feature,
                                                                                         app):
        # Given
        mock_feature.side_effect = [
            True, False
        ]

        # When
        pc_update_recommendations_view(app)

        # Then
        assert mock_feature.call_count == 2
        mock_discovery_refresh.assert_called_once()

    @patch('scheduled_tasks.clock.feature_queries.is_active')
    @patch('scheduled_tasks.clock.discovery_view_queries.refresh')
    def test_should_not_call_refresh_view_when_recommendation_with_geolocation_is_active(self,
                                                                                         mock_discovery_refresh,
                                                                                         mock_feature,
                                                                                         app):
        # Given
        mock_feature.side_effect = [
            True, True
        ]

        # When
        pc_update_recommendations_view(app)

        # Then
        assert mock_feature.call_count == 2
        mock_discovery_refresh.assert_not_called()


class PcCleanDiscoveryViewsTest:
    @patch('scheduled_tasks.clock.feature_queries.is_active')
    @patch('scheduled_tasks.clock.discovery_view_queries.clean')
    @patch('scheduled_tasks.clock.discovery_view_v3_queries.clean')
    def test_should_call_discovery_view_v3_clean_when_feature_is_active(self,
                                                                        mock_discovery_v3_clean,
                                                                        mock_discovery_clean,
                                                                        mock_feature,
                                                                        app):
        # Given
        mock_feature.side_effect = [
            True, True
        ]

        # When
        pc_clean_discovery_views(app)

        # Then
        mock_discovery_v3_clean.assert_called_once_with(app)
        mock_discovery_clean.assert_not_called()

    @patch('scheduled_tasks.clock.feature_queries.is_active')
    @patch('scheduled_tasks.clock.discovery_view_queries.clean')
    @patch('scheduled_tasks.clock.discovery_view_v3_queries.clean')
    def test_should_call_discovery_view_v1_clean_when_geoloc_feature_is_not_active(self,
                                                                                   mock_discovery_v3_clean,
                                                                                   mock_discovery_clean,
                                                                                   mock_feature,
                                                                                   app):
        # Given
        mock_feature.side_effect = [
            True, False
        ]

        # When
        pc_clean_discovery_views(app)

        # Then
        mock_discovery_clean.assert_called_once_with(app)
        mock_discovery_v3_clean.assert_not_called()


class PcArchiveTrackingDataTest:
    @patch.dict('os.environ', {})
    @patch('scheduled_tasks.clock.run_matomo_archiving')
    def test_do_not_archive_tracking_data_when_server_and_token_are_not_defined(self,
                                                                                mock_run_matomo_archiving,
                                                                                app):
        # When
        archive_tracking_data(app)

        # Then
        mock_run_matomo_archiving.assert_not_called()

    @patch.dict('os.environ', {'MATOMO_AUTH_TOKEN': 'XYZ', 'MATOMO_SERVER_URL': 'server_url'})
    @patch('scheduled_tasks.clock.run_matomo_archiving')
    def test_archive_tracking_data_when_server_and_token_are_defined(self,
                                                                     mock_run_matomo_archiving,
                                                                     app):
        # When
        archive_tracking_data(app)

        # Then
        mock_run_matomo_archiving.assert_called_once_with('server_url', 'XYZ')