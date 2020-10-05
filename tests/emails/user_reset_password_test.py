from unittest.mock import patch

from emails.user_reset_password import retrieve_data_for_reset_password_user_email
from repository import repository
from tests.model_creators.generic_creators import create_user, create_offerer, create_user_offerer
import pytest
from tests.conftest import clean_database


class MakeUserResetPasswordEmailDataTest:
    @patch('emails.user_reset_password.SUPPORT_EMAIL_ADDRESS', 'support@example.com')
    @patch('emails.user_reset_password.DEV_EMAIL_ADDRESS', 'dev@example.com')
    @patch('emails.user_reset_password.format_environment_for_email', return_value='-testing')
    @patch('emails.user_reset_password.feature_send_mail_to_users_enabled', return_value=False)
    @clean_database
    @pytest.mark.usefixtures("db_session")
    def test_email_is_sent_to_dev_at_passculture_when_not_production_environment(self,
                                                                                 mock_send_mail_enabled,
                                                                                 mock_format_env,
                                                                                 app
                                                                                 ):
        # Given
        user = create_user(email="ewing@example.com", first_name='Bobby', reset_password_token='ABCDEFG')
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)

        repository.save(user_offerer)

        # When
        reset_password_email_data = retrieve_data_for_reset_password_user_email(user=user)

        # Then
        assert reset_password_email_data == {
            'FromEmail': 'support@example.com',
            'MJ-TemplateID': 912168,
            'MJ-TemplateLanguage': True,
            'To': 'dev@example.com',
            'Vars':
                {
                    'prenom_user': 'Bobby',
                    'token': user.resetPasswordToken,
                    'env': '-testing'
                }
        }

    @patch('emails.user_reset_password.SUPPORT_EMAIL_ADDRESS', 'support@example.com')
    @patch('emails.user_reset_password.format_environment_for_email', return_value='')
    @patch('emails.user_reset_password.feature_send_mail_to_users_enabled', return_value=True)
    @pytest.mark.usefixtures("db_session")
    def test_email_is_sent_to_pro_offerer_when_production_environment(self,
                                                                      mock_send_mail_enabled,
                                                                      mock_format_env,
                                                                      app):
        # Given
        user = create_user(email="ewing@example.com", first_name='Bobby', reset_password_token='ABCDEFG')
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer)

        repository.save(user_offerer)

        # When
        reset_password_email_data = retrieve_data_for_reset_password_user_email(user=user)

        # Then
        assert reset_password_email_data == {
            'FromEmail': 'support@example.com',
            'MJ-TemplateID': 912168,
            'MJ-TemplateLanguage': True,
            'To': 'ewing@example.com',
            'Vars':
                {
                    'prenom_user': 'Bobby',
                    'token': user.resetPasswordToken,
                    'env': ''
                }
        }
