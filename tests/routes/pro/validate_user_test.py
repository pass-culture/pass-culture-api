from unittest.mock import patch

import pytest

from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.models import Offerer
from pcapi.models import UserOfferer
from pcapi.models import UserSQLEntity
from pcapi.repository import repository

from tests.conftest import TestClient


class Patch:
    class Returns204:
        @pytest.mark.usefixtures("db_session")
        def expect_validation_token_to_be_set_to_none_and_email_validated(self, app):
            # Given
            user = create_user()
            user.generate_validation_token()
            repository.save(user)
            user_id = user.id

            # When
            response = TestClient(app.test_client()).patch(
                f"/validate/user/{user.validationToken}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            validated_user = UserSQLEntity.query.get(user_id)
            assert response.status_code == 204
            assert validated_user.isValidated
            assert validated_user.isEmailValidated

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.validate.send_ongoing_offerer_attachment_information_email_to_pro", return_value=True)
        @patch("pcapi.routes.pro.validate.send_raw_email", return_value=True)
        def test_send_ongoing_offerer_attachment_information_email_to_pro(
            self, mock_send_raw_email, mock_send_ongoing_offerer_attachment_information_email_to_pro, app
        ):
            # Given
            user = create_user()
            user2 = create_user(email="pro2@example.com")
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            user_offerer2 = create_user_offerer(user2, offerer)

            user.generate_validation_token()

            repository.save(user_offerer, user_offerer2)

            # When
            response = TestClient(app.test_client()).patch(
                f"/validate/user/{user.validationToken}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 204
            mock_send_ongoing_offerer_attachment_information_email_to_pro.assert_called_once_with(
                user_offerer, mock_send_raw_email
            )

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.routes.pro.validate.send_pro_user_waiting_for_validation_by_admin_email", return_value=True)
        @patch("pcapi.routes.pro.validate.send_raw_email", return_value=True)
        def test_send_pro_user_waiting_for_validation_by_admin_email(
            self, mock_send_raw_email, mock_send_pro_user_waiting_for_validation_by_admin_email, app
        ):
            # Given
            user = create_user()
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)

            user.generate_validation_token()

            repository.save(user_offerer)

            # When
            response = TestClient(app.test_client()).patch(
                f"/validate/user/{user.validationToken}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 204
            mock_send_pro_user_waiting_for_validation_by_admin_email.assert_called_once_with(
                user, mock_send_raw_email, offerer
            )

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.settings.IS_INTEGRATION", False)
        @patch("pcapi.routes.pro.validate.maybe_send_offerer_validation_email", return_value=True)
        @patch("pcapi.routes.pro.validate.send_raw_email", return_value=True)
        def test_maybe_send_offerer_validation_email_when_not_in_integration_env(
            self, mock_send_raw_email, mock_maybe_send_offerer_validation_email, app
        ):
            # Given
            pro = create_user()
            offerer = create_offerer(siren="775671464")
            user_offerer = create_user_offerer(pro, offerer)

            pro.generate_validation_token()

            repository.save(user_offerer)

            # When
            response = TestClient(app.test_client()).patch(
                f"/validate/user/{pro.validationToken}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 204
            mock_maybe_send_offerer_validation_email.assert_called_once_with(offerer, user_offerer, mock_send_raw_email)

        @pytest.mark.usefixtures("db_session")
        @patch("pcapi.settings.IS_INTEGRATION", True)
        @patch("pcapi.routes.pro.validate.maybe_send_offerer_validation_email", return_value=True)
        def test_validate_offerer_and_user_offerer_when_in_integration_env(
            self, mock_maybe_send_offerer_validation_email, app
        ):
            # Given
            pro = create_user()
            offerer = create_offerer()
            user_offerer = create_user_offerer(pro, offerer)

            pro.generate_validation_token()

            repository.save(user_offerer)

            # When
            response = TestClient(app.test_client()).patch(
                f"/validate/user/{pro.validationToken}", headers={"origin": "http://localhost:3000"}
            )

            # Then
            assert response.status_code == 204
            assert mock_maybe_send_offerer_validation_email.call_count == 0
            offerer = Offerer.query.first()
            user_offerer = UserOfferer.query.first()
            assert offerer.validationToken is None
            assert user_offerer.validationToken is None


class Returns404:
    @pytest.mark.usefixtures("db_session")
    def when_validation_token_is_not_found(self, app):
        # Given
        random_token = "0987TYGHHJMJ"

        # When
        response = TestClient(app.test_client()).patch(
            f"/validate/user/{random_token}", headers={"origin": "http://localhost:3000"}
        )

        # Then
        assert response.status_code == 404
        assert response.json["global"] == ["Ce lien est invalide"]
