from unittest.mock import patch, MagicMock

from scheduled_tasks.decorators import cron_context, cron_require_feature


class CronContextTest:
    def test_should_give_app_context_to_decorated_function(self):
        # Given
        @cron_context
        def decorated_function(*args):
            return 'expected result'

        application = MagicMock()
        application.app_context.return_value = MagicMock()

        # When
        result = decorated_function(application)

        # Then
        assert result == 'expected result'
        application.app_context.assert_called_once()


class CronRequireFeatureTest:
    @patch('scheduled_tasks.decorators.feature_queries.is_active', return_value=True)
    def test_should_execute_function_when_feature_is_active(self, mock_active_feature):
        # Given
        @cron_require_feature('feature')
        def decorated_function(*args):
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
        def decorated_function(*args):
            return 'expected result'

        # When
        result = decorated_function()

        # Then
        assert result is None
        mock_logger.assert_called_once_with('feature is not active')
