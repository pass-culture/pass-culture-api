from unittest.mock import patch

from emails.user_reset_password import retrieve_data_for_reset_password_email
from tests.model_creators.generic_creators import create_user


class MakeResetPasswordEmailDataTest:
    @patch('emails.user_reset_password.SUPPORT_EMAIL_ADDRESS', 'support@example.com')
    @patch('emails.user_reset_password.format_environment_for_email', return_value='-testing')
    @patch('emails.user_reset_password.feature_send_mail_to_users_enabled', return_value=False)
    def test_email_is_sent_to_dev_at_passculture_when_not_production_environment(self, mock_send_mail_enabled,
                                                                                mock_format_env):
        # Given
        user = create_user(email="johnny.wick@example.com", first_name="Johnny", reset_password_token='ABCDEFG')

        # When
        reset_password_email_data = retrieve_data_for_reset_password_email(user=user)

        # Then
        assert reset_password_email_data == {
            'FromEmail': 'support@example.com',
            'MJ-TemplateID': 912168,
            'MJ-TemplateLanguage': True,
            'To': 'dev@passculture.app',
            'Vars':
                {
                    'prenom_user': 'Johnny',
                    'token': 'ABCDEFG',
                    'env': '-testing'
                }
        }

    @patch('emails.user_reset_password.SUPPORT_EMAIL_ADDRESS', 'support@example.com')
    @patch('emails.user_reset_password.format_environment_for_email', return_value='')
    @patch('emails.user_reset_password.feature_send_mail_to_users_enabled', return_value=True)
    def test_email_is_sent_to_user_when_production_environment(self, mock_send_mail_enabled,
                                                                            mock_format_env):
        # Given
        user = create_user(email="johnny.wick@example.com", first_name="Johnny", reset_password_token='ABCDEFG')

        # When
        reset_password_email_data = retrieve_data_for_reset_password_email(user=user)

        # Then
        assert reset_password_email_data == {
            'FromEmail': 'support@example.com',
            'MJ-TemplateID': 912168,
            'MJ-TemplateLanguage': True,
            'To': 'johnny.wick@example.com',
            'Vars':
                {
                    'prenom_user': 'Johnny',
                    'token': 'ABCDEFG',
                    'env': ''
                }
        }
