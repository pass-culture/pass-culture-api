from flask_login import AnonymousUserMixin
import pytest

from pcapi.core.users.models import UserSQLEntity
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_user_offerer
from pcapi.models import ApiErrors
from pcapi.models import ApiKey
from pcapi.repository import repository
from pcapi.utils.token import random_token
from pcapi.validation.routes.users_authorizations import check_api_key_allows_to_validate_booking
from pcapi.validation.routes.users_authorizations import check_user_can_validate_activation_offer
from pcapi.validation.routes.users_authorizations import check_user_can_validate_bookings
from pcapi.validation.routes.users_authorizations import check_user_can_validate_bookings_v2


class CheckUserCanValidateBookingTest:
    @pytest.mark.usefixtures("db_session")
    def test_check_user_can_validate_bookings_returns_true_when_user_is_authenticated_and_has_editor_rights_on_booking(
        self, app
    ):
        # Given
        user = create_user()
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer, None)
        repository.save(user, offerer, user_offerer)

        # When
        result = check_user_can_validate_bookings(user, offerer.id)

        # Then
        assert result is True

    def test_check_user_can_validate_bookings_returns_false_when_user_is_not_logged_in(self, app):
        # Given
        user = AnonymousUserMixin()

        # When
        result = check_user_can_validate_bookings(user, None)

        # Then
        assert result is False

    def test_check_user_can_validate_bookings_raise_api_error_when_user_is_authenticated_and_does_not_have_editor_rights_on_booking(
        self, app
    ):
        # Given
        user = UserSQLEntity()
        user.is_authenticated = True

        # When
        with pytest.raises(ApiErrors) as errors:
            check_user_can_validate_bookings(user, None)

        # Then
        assert errors.value.errors["global"] == ["Cette contremarque n'a pas été trouvée"]


class CheckUserCanValidateBookingTestv2:
    @pytest.mark.usefixtures("db_session")
    def test_does_not_raise_error_when_user_has_editor_rights_on_booking(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer, None)

        repository.save(user, offerer, user_offerer)

        # Then the following should not raise
        check_user_can_validate_bookings_v2(user, offerer.id)

    def test_check_user_can_validate_v2_bookings_raise_api_error_when_user_is_authenticated_but_does_not_have_editor_rights_on_booking(
        self, app
    ):
        # Given
        user = UserSQLEntity()
        user.is_authenticated = True

        # When
        with pytest.raises(ApiErrors) as errors:
            check_user_can_validate_bookings_v2(user, None)

        # Then
        assert errors.value.errors["user"] == ["Vous n'avez pas les droits suffisants pour valider cette contremarque."]


class CheckApiKeyAllowsToValidateBookingTest:
    @pytest.mark.usefixtures("db_session")
    def test_does_not_raise_error_when_api_key_is_provided_and_is_related_to_offerer_id(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        user_offerer = create_user_offerer(user, offerer, None)

        repository.save(user, offerer, user_offerer)

        validApiKey = ApiKey()
        validApiKey.value = random_token(64)
        validApiKey.offererId = offerer.id

        repository.save(validApiKey)

        # The the following should not raise
        check_api_key_allows_to_validate_booking(validApiKey, offerer.id)

    def test_raises_exception_when_api_key_is_provided_but_related_offerer_does_not_have_rights_on_booking(self, app):
        # Given
        validApiKey = ApiKey()
        validApiKey.value = random_token(64)
        validApiKey.offererId = 67

        # When
        with pytest.raises(ApiErrors) as errors:
            check_api_key_allows_to_validate_booking(validApiKey, None)

        # Then
        assert errors.value.errors["user"] == ["Vous n'avez pas les droits suffisants pour valider cette contremarque."]


class CheckUserCanValidateActivationOfferTest:
    @pytest.mark.usefixtures("db_session")
    def test_does_not_raise_error_when_user_is_admin(self, app):
        # Given
        admin_user = create_user(is_admin=True)

        # The the following should not raise
        check_user_can_validate_activation_offer(admin_user)

    def test_raises_exception_when_user_is_not_admin(self, app):
        # Given
        user = create_user()

        # When
        with pytest.raises(ApiErrors) as errors:
            check_user_can_validate_activation_offer(user)

        # Then
        assert errors.value.errors["user"] == ["Vous n'avez pas les droits suffisants pour valider cette contremarque."]
