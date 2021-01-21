from datetime import date
from datetime import datetime
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
import jwt
import pytest

from pcapi import settings
from pcapi.core.users import api as users_api
from pcapi.core.users import constants as users_constants
from pcapi.core.users import exceptions as users_exceptions
from pcapi.core.users import factories as users_factories
from pcapi.core.users.api import create_email_validation_token
from pcapi.core.users.api import create_id_check_token
from pcapi.core.users.api import create_reset_password_token
from pcapi.core.users.api import get_user_from_jwt_token
from pcapi.core.users.models import ALGORITHM_HS_256
from pcapi.core.users.models import TokenType
from pcapi.core.users.models import User
from pcapi.core.users.utils import encode_jwt_payload
from pcapi.models.user_session import UserSession
from pcapi.repository import repository


pytestmark = pytest.mark.usefixtures("db_session")


class ValidateJwtTokenTest:
    def test_get_user_with_valid_token(self):
        user = users_factories.UserFactory()
        repository.save(user)
        token_type = TokenType.RESET_PASSWORD
        expiration_date = datetime.now() + timedelta(hours=24)

        token_payload = encode_jwt_payload({"type": token_type.value, "userId": user.id}, expiration_date)

        associated_user = get_user_from_jwt_token(token_payload, token_type)

        assert associated_user.id == user.id

    def test_get_user_with_valid_token_without_expiration_date(self):
        user = users_factories.UserFactory()
        repository.save(user)
        token_type = TokenType.ID_CHECK
        token_payload = encode_jwt_payload({"type": token_type.value, "userId": user.id})

        associated_user = get_user_from_jwt_token(token_payload, token_type)

        assert associated_user.id == user.id

    def test_get_user_with_valid_token_token_encoded_with_wrong_key(self):
        user = users_factories.UserFactory()
        repository.save(user)
        token_type = TokenType.ID_CHECK
        token_payload = jwt.encode(
            {"type": token_type.value, "userId": user.id},
            "wrong-key",
            algorithm=ALGORITHM_HS_256,
        ).decode("ascii")

        associated_user = get_user_from_jwt_token(token_payload, token_type)

        assert not associated_user

    def test_get_user_with_valid_token_wrong_type(self):
        user = users_factories.UserFactory()
        repository.save(user)
        token_type = TokenType.ID_CHECK
        token_payload = encode_jwt_payload({"type": "other-value", "userId": user.id})

        associated_user = get_user_from_jwt_token(token_payload, token_type)

        assert not associated_user

    def test_get_user_with_valid_token_with_expired_date(self):
        user = users_factories.UserFactory()
        repository.save(user)
        token_type = TokenType.RESET_PASSWORD
        expiration_date = datetime.now() - timedelta(hours=24)

        token_payload = encode_jwt_payload({"type": token_type.value, "userId": user.id}, expiration_date)

        associated_user = get_user_from_jwt_token(token_payload, token_type)

        assert associated_user is None


class CreateEmailValidationToken:
    def test_create_email_validation_token(self):
        user = users_factories.UserFactory(dateOfBirth=datetime(2000, 1, 1))

        token, expiration_date = create_email_validation_token(user)

        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)
        assert decoded["userId"] == user.id
        assert decoded["type"] == TokenType.EMAIL_VALIDATION.value
        assert decoded["exp"] == int(expiration_date.timestamp())
        assert decoded["exp"] > datetime.utcnow().timestamp()


class CreateResetPasswordToken:
    def test_create_reset_password_token(self):
        user = users_factories.UserFactory(dateOfBirth=datetime(2000, 1, 1))

        token, expiration_date = create_reset_password_token(user)

        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)
        assert decoded["userId"] == user.id
        assert decoded["type"] == TokenType.RESET_PASSWORD.value
        assert decoded["exp"] == int(expiration_date.timestamp())
        assert decoded["exp"] > datetime.utcnow().timestamp()


class GenerateIdCheckTokenIfEligibleTest:
    @freeze_time("2018-06-01")
    def test_when_elible(self):
        user = users_factories.UserFactory(dateOfBirth=datetime(2000, 1, 1))

        token, expiration_date = create_id_check_token(user)

        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=ALGORITHM_HS_256)
        assert decoded["userId"] == user.id
        assert decoded["type"] == TokenType.ID_CHECK.value
        assert decoded["exp"] == int(expiration_date.timestamp())
        assert decoded["exp"] > datetime.utcnow().timestamp()

    @freeze_time("2018-06-01")
    def test_when_not_elible_under_age(self):
        # user is 17 years old
        user = users_factories.UserFactory(dateOfBirth=datetime(2000, 8, 1))
        token = create_id_check_token(user)
        assert not token

    @freeze_time("2018-06-01")
    def test_when_not_elible_above_age(self):
        # user is 19 years old
        user = users_factories.UserFactory(dateOfBirth=datetime(1999, 5, 1))
        token = create_id_check_token(user)
        assert not token


class SuspendAccountTest:
    def test_suspend_account(self):
        user = users_factories.UserFactory(isAdmin=True)
        users_factories.UserSessionFactory(user=user)
        reason = users_constants.SuspensionReason.FRAUD
        actor = users_factories.UserFactory(isAdmin=True)

        users_api.suspend_account(user, reason, actor)

        assert user.suspensionReason == str(reason)
        assert not user.isActive
        assert not user.isAdmin
        assert not UserSession.query.filter_by(userId=user.id).first()
        assert actor.isActive


class UnsuspendAccountTest:
    def test_unsuspend_account(self):
        user = users_factories.UserFactory(isActive=False)
        actor = users_factories.UserFactory(isAdmin=True)

        users_api.unsuspend_account(user, actor)

        assert not user.suspensionReason
        assert user.isActive


@pytest.mark.usefixtures("db_session")
class ChangeUserEmailTest:
    @freeze_time("2020-10-15 09:00:00")
    def test_change_user_email(self):
        # Given
        user = users_factories.UserFactory(email="oldemail@mail.com", firstName="UniqueNameForEmailChangeTest")
        users_factories.UserSessionFactory(user=user)
        expiration_date = datetime.now() + timedelta(hours=1)
        token_payload = dict(
            current_email="oldemail@mail.com", new_email="newemail@mail.com", type=TokenType.CHANGE_EMAIL.value
        )
        token = encode_jwt_payload(token_payload, expiration_date)

        # When
        users_api.change_user_email(token)

        # Then
        assert user.email == "newemail@mail.com"
        new_user = User.query.filter_by(email="newemail@mail.com").first()
        assert new_user is not None
        assert new_user.firstName == "UniqueNameForEmailChangeTest"
        old_user = User.query.filter_by(email="oldemail@mail.com").first()
        assert old_user is None
        assert UserSession.query.filter_by(userId=user.id).first() is None

    def test_change_user_email_undecodable_token(self):
        # Given
        users_factories.UserFactory(email="oldemail@mail.com", firstName="UniqueNameForEmailChangeTest")
        token = "wtftokenwhatareyoutryingtodo"

        # When
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            users_api.change_user_email(token)

        # Then
        old_user = User.query.filter_by(email="oldemail@mail.com").first()
        assert old_user is not None
        new_user = User.query.filter_by(email="newemail@mail.com").first()
        assert new_user is None

    @freeze_time("2020-10-15 09:00:00")
    def test_change_user_email_expired_token(self):
        # Given
        users_factories.UserFactory(email="oldemail@mail.com", firstName="UniqueNameForEmailChangeTest")
        expiration_date = datetime.now() - timedelta(hours=1)
        token_payload = dict(
            current_email="oldemail@mail.com", new_email="newemail@mail.com", type=TokenType.CHANGE_EMAIL.value
        )
        token = encode_jwt_payload(token_payload, expiration_date)

        # When
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            users_api.change_user_email(token)

        # Then
        old_user = User.query.filter_by(email="oldemail@mail.com").first()
        assert old_user is not None
        new_user = User.query.filter_by(email="newemail@mail.com").first()
        assert new_user is None

    @freeze_time("2020-10-15 09:00:00")
    def test_change_user_email_missing_argument_in_token(self):
        # Given
        users_factories.UserFactory(email="oldemail@mail.com", firstName="UniqueNameForEmailChangeTest")
        expiration_date = datetime.now() + timedelta(hours=1)
        missing_current_email_token_payload = dict(new_email="newemail@mail.com", type=TokenType.CHANGE_EMAIL.value)
        missing_current_email_token = encode_jwt_payload(missing_current_email_token_payload, expiration_date)

        missing_new_email_token_payload = dict(current_email="oldemail@mail.com", type=TokenType.CHANGE_EMAIL.value)
        missing_new_email_token = encode_jwt_payload(missing_new_email_token_payload, expiration_date)

        missing_exp_token_payload = dict(new_email="newemail@mail.com", type=TokenType.CHANGE_EMAIL.value)
        missing_exp_token = encode_jwt_payload(missing_exp_token_payload)

        missing_type_token_payload = dict(new_email="newemail@mail.com", current_email="oldemail@mail.com")
        missing_type_token = encode_jwt_payload(missing_type_token_payload, expiration_date)

        # When
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            users_api.change_user_email(missing_current_email_token)
            users_api.change_user_email(missing_new_email_token)
            users_api.change_user_email(missing_exp_token)
            users_api.change_user_email(missing_type_token)

        # Then
        old_user = User.query.filter_by(email="oldemail@mail.com").first()
        assert old_user is not None
        new_user = User.query.filter_by(email="newemail@mail.com").first()
        assert new_user is None

    @freeze_time("2020-10-15 09:00:00")
    def test_change_user_email_new_email_already_existing(self):
        # Given
        users_factories.UserFactory(email="newemail@mail.com", firstName="UniqueNameForEmailChangeTest")
        expiration_date = datetime.now() + timedelta(hours=1)
        token_payload = dict(
            current_email="oldemail@mail.com", new_email="newemail@mail.com", type=TokenType.CHANGE_EMAIL.value
        )
        token = encode_jwt_payload(token_payload, expiration_date)

        # When
        users_api.change_user_email(token)

        # Then
        old_user = User.query.filter_by(email="oldemail@mail.com").first()
        assert old_user is None
        new_user = User.query.filter_by(email="newemail@mail.com").first()
        assert new_user is not None

    @freeze_time("2020-10-15 09:00:00")
    def test_change_user_email_current_email_not_existing_anymore(self):
        # Given
        expiration_date = datetime.now() + timedelta(hours=1)
        token_payload = dict(
            current_email="oldemail@mail.com", new_email="newemail@mail.com", type=TokenType.CHANGE_EMAIL.value
        )
        token = encode_jwt_payload(token_payload, expiration_date)

        # When
        users_api.change_user_email(token)

        # Then
        old_user = User.query.filter_by(email="oldemail@mail.com").first()
        assert old_user is None
        new_user = User.query.filter_by(email="newemail@mail.com").first()
        assert new_user is None


class CreateBeneficiaryTest:
    def test_with_ineligible_user_raises_exception(self):
        user = users_factories.UserFactory.build(isBeneficiary=False)
        with pytest.raises(users_exceptions.NotEligible):
            users_api.activate_beneficiary(user, "test")

    def test_with_eligible_user(self):
        eligible_date = date.today() - relativedelta(years=18, days=30)
        user = users_factories.UserFactory(isBeneficiary=False, dateOfBirth=eligible_date)
        user = users_api.activate_beneficiary(user, "test")
        assert user.isBeneficiary
        assert len(user.deposits) == 1
