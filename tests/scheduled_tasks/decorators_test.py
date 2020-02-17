from unittest.mock import patch

from scheduled_tasks.decorators import cron_require_feature


class CronRequireFeatureTest:
    @patch('scheduled_tasks.decorators.feature_queries.is_active', return_value=True)
    def test_cron_require_feature(self, mock_active_feature):
        # Given
        @cron_require_feature('feature')
        def decorated_function():
            return 'expected result'

        # When
        result = decorated_function()

        # Then
        assert result == 'expected result'

    @patch('scheduled_tasks.decorators.logger.info')
    @patch('scheduled_tasks.decorators.feature_queries.is_active', return_value=False)
    def when_feature_is_not_activated_raise_an_error(self, mock_not_active_feature, mock_logger):
        # Given
        @cron_require_feature('feature')
        def decorated_function():
            return 'expected result'

        # When
        result = decorated_function()

        # Then
        assert result is None
        mock_logger.assert_called_once_with('decorated_function is not active')
