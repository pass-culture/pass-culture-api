from unittest.mock import patch

from sqlalchemy.exc import IntegrityError

from pcapi.model_creators.generic_creators import create_user
from pcapi.models import ApiErrors
from pcapi.validation.models.user import validate


class UserAlreadyExistsTest:
    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_return_error_when_email_already_exist_in_database_but_no_id_is_provided(
        self, mocked_count_users_by_email, app
    ):
        # Given
        user = create_user(idx=None)
        mocked_count_users_by_email.return_value = 1
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors["email"] == ["Un compte lié à cet e-mail existe déjà"]

    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_not_return_error_when_email_already_exist_in_database_but_id_is_provided(
        self, mocked_count_users_by_email, app
    ):
        # Given
        user = create_user(idx=1)
        mocked_count_users_by_email.return_value = 1
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors == {}

    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_return_error_when_user_count_raise_error_and_no_id_is_provided(
        self, mocked_count_users_by_email, app
    ):
        # Given
        user = create_user(idx=None)
        mocked_count_users_by_email.side_effect = IntegrityError("Mock", "mock", "mock")
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors["email"] == ["Un compte lié à cet e-mail existe déjà"]

    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_not_return_error_when_user_count_raise_error_and_id_is_provided(
        self, mocked_count_users_by_email, app
    ):
        # Given
        user = create_user(idx=1)
        mocked_count_users_by_email.return_value = IntegrityError("mock", "mock", "mock")
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors == {}


class PublicNameTest:
    def test_should_return_error_message_when_user_public_name_is_empty(self, app):
        # Given
        user = create_user(public_name="")
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors["publicName"] == ["Tu dois saisir au moins 1 caractères."]

    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_not_return_error_message_when_user_public_name_is_correct(self, mocked_count_users_by_email, app):
        # Given
        user = create_user(public_name="Jo")
        mocked_count_users_by_email.return_value = 0
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors == {}


class EmailTest:
    def test_should_return_error_message_when_email_does_not_contain_at_sign(self, app):
        # Given
        user = create_user(email="joel.example.com")
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors["email"] == ["L’e-mail doit contenir un @."]

    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_not_return_error_message_when_user_email_is_correct(self, mocked_count_users_by_email, app):
        # Given
        user = create_user(email="joel@example.com")
        mocked_count_users_by_email.return_value = 0
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors == {}


class AdminTest:
    def test_should_return_error_message_when_admin_user_is_beneficiary(self, app):
        # Given
        user = create_user(is_admin=True, is_beneficiary=True)
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors["isBeneficiary"] == ["Admin ne peut pas être bénéficiaire"]


class PasswordTest:
    def test_should_return_error_message_when_user_password_is_less_than_8_characters(self, app):
        # Given
        user = create_user(password="Jo")
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors["password"] == ["Tu dois saisir au moins 8 caractères."]

    @patch("pcapi.validation.models.user.user_queries.count_users_by_email")
    def test_should_not_return_error_message_when_user_password_is_correct(self, mocked_count_users_by_email, app):
        # Given
        user = create_user(password="JoelDupont")
        mocked_count_users_by_email.return_value = 0
        api_errors = ApiErrors()

        # When
        api_error = validate(user, api_errors)

        # Then
        assert api_error.errors == {}
