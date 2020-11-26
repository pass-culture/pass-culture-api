from unittest.mock import patch

import pytest

from pcapi.emails.pro_reset_password import retrieve_data_for_reset_password_pro_email
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.repository import repository


class MakeProResetPasswordEmailDataTest:
    @patch("pcapi.emails.pro_reset_password.format_environment_for_email", return_value="-testing")
    @patch("pcapi.emails.pro_reset_password.feature_send_mail_to_users_enabled", return_value=False)
    @patch("pcapi.settings.PRO_URL", "http://example.net")
    @pytest.mark.usefixtures("db_session")
    def test_email_is_sent_to_dev_at_passculture_when_not_production_environment(
        self, mock_send_mail_enabled, mock_format_env, app
    ):
        # Given
        pro = create_user(email="pro@example.com", reset_password_token="ABCDEFG")
        offerer = create_offerer()
        user_offerer = create_user_offerer(pro, offerer)

        repository.save(user_offerer)

        # When
        reset_password_email_data = retrieve_data_for_reset_password_pro_email(user=pro)

        # Then
        assert reset_password_email_data == {
            "FromEmail": "support@example.com",
            "MJ-TemplateID": 779295,
            "MJ-TemplateLanguage": True,
            "To": "dev@example.com",
            "Vars": {"lien_nouveau_mdp": "http://example.net/mot-de-passe-perdu?token=ABCDEFG", "env": "-testing"},
        }

    @patch("pcapi.emails.pro_reset_password.format_environment_for_email", return_value="")
    @patch("pcapi.emails.pro_reset_password.feature_send_mail_to_users_enabled", return_value=True)
    @patch("pcapi.settings.PRO_URL", "http://example.net")
    @pytest.mark.usefixtures("db_session")
    def test_email_is_sent_to_pro_offerer_when_production_environment(
        self, mock_send_mail_enabled, mock_format_env, app
    ):
        # Given
        pro = create_user(email="pro@example.com", reset_password_token="ABCDEFG")
        offerer = create_offerer()
        user_offerer = create_user_offerer(pro, offerer)

        repository.save(user_offerer)

        # When
        reset_password_email_data = retrieve_data_for_reset_password_pro_email(user=pro)

        # Then
        assert reset_password_email_data == {
            "FromEmail": "support@example.com",
            "MJ-TemplateID": 779295,
            "MJ-TemplateLanguage": True,
            "To": "pro@example.com",
            "Vars": {"lien_nouveau_mdp": "http://example.net/mot-de-passe-perdu?token=ABCDEFG", "env": ""},
        }
