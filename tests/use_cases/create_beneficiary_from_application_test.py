from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time
import pytest

from pcapi.core.testing import override_features
from pcapi.core.testing import override_settings
from pcapi.core.users import api as users_api
from pcapi.core.users.models import TokenType
from pcapi.core.users.models import User
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription import BeneficiaryPreSubscription
from pcapi.domain.beneficiary_pre_subscription.beneficiary_pre_subscription_exceptions import BeneficiaryIsADuplicate
from pcapi.model_creators.generic_creators import create_user
from pcapi.models import BeneficiaryImport
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.models.deposit import Deposit
from pcapi.notifications.push import testing as push_testing
from pcapi.repository import repository
from pcapi.use_cases.create_beneficiary_from_application import create_beneficiary_from_application


PRE_SUBSCRIPTION_BASE_DATA = {
    "activity": "Apprenti",
    "address": "3 rue de Valois",
    "city": "Paris",
    "civility": "Mme",
    "date_of_birth": datetime(1995, 2, 5),
    "email": "rennes@example.org",
    "first_name": "Thomas",
    "last_name": "DURAND",
    "phone_number": "0123456789",
    "source": "jouve",
    "source_id": None,
}


class FakeBeneficiaryJouveBackend:
    def get_application_by(self, application_id: int) -> BeneficiaryPreSubscription:
        return BeneficiaryPreSubscription(
            application_id=application_id,
            postal_code=f"{application_id:02d}123",
            **PRE_SUBSCRIPTION_BASE_DATA,
        )


@patch("pcapi.use_cases.create_beneficiary_from_application.send_activation_email")
@patch("pcapi.domain.password.random_token")
@patch(
    "pcapi.settings.JOUVE_APPLICATION_BACKEND",
    "tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend",
)
@freeze_time("2013-05-15 09:00:00")
@pytest.mark.usefixtures("db_session")
def test_saved_a_beneficiary_from_application(stubed_random_token, mocked_send_activation_email, app):
    # Given
    application_id = 35
    stubed_random_token.return_value = "token"

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    beneficiary = User.query.one()
    assert beneficiary.activity == "Apprenti"
    assert beneficiary.address == "3 rue de Valois"
    assert beneficiary.isBeneficiary is True
    assert beneficiary.city == "Paris"
    assert beneficiary.civility == "Mme"
    assert beneficiary.dateOfBirth == datetime(1995, 2, 5)
    assert beneficiary.departementCode == "35"
    assert beneficiary.email == "rennes@example.org"
    assert beneficiary.firstName == "Thomas"
    assert beneficiary.hasSeenTutorials is False
    assert beneficiary.isAdmin is False
    assert beneficiary.lastName == "DURAND"
    assert beneficiary.password is not None
    assert beneficiary.phoneNumber == "0123456789"
    assert beneficiary.postalCode == "35123"
    assert beneficiary.publicName == "Thomas DURAND"
    assert beneficiary.notificationSubscriptions == {"marketing_push": True, "marketing_email": True}

    deposit = Deposit.query.one()
    assert deposit.amount == 500
    assert deposit.source == "dossier jouve [35]"
    assert deposit.userId == beneficiary.id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary == beneficiary

    assert len(beneficiary.tokens) == 1
    assert beneficiary.tokens[0].type == TokenType.RESET_PASSWORD

    mocked_send_activation_email.assert_called_once()

    assert push_testing.requests == [
        {
            "user_id": beneficiary.id,
            "attribute_values": {
                "u.credit": 50000,
                "date(u.date_of_birth)": "1995-02-05T00:00:00",
                "u.postal_code": "35123",
                "date(u.date_created)": beneficiary.dateCreated.strftime("%Y-%m-%dT%H:%M:%S"),
                "u.marketing_push_subscription": True,
                "u.is_beneficiary": True,
                "date(u.deposit_expiration_date)": "2015-05-15T09:00:00",
            },
        }
    ]


@patch("pcapi.use_cases.create_beneficiary_from_application.send_accepted_as_beneficiary_email")
@patch(
    "pcapi.settings.JOUVE_APPLICATION_BACKEND",
    "tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend",
)
@freeze_time("2013-05-15 09:00:00")
@pytest.mark.usefixtures("db_session")
def test_application_for_native_app_user(mocked_send_accepted_as_beneficiary_email, app):
    # Given
    application_id = 35
    users_api.create_account(
        email=PRE_SUBSCRIPTION_BASE_DATA["email"],
        password="123456789",
        birthdate=PRE_SUBSCRIPTION_BASE_DATA["date_of_birth"],
        is_email_validated=True,
        send_activation_mail=False,
        marketing_email_subscription=False,
    )
    push_testing.reset_requests()

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    mocked_send_accepted_as_beneficiary_email.assert_called_once()

    beneficiary = User.query.one()
    deposit = Deposit.query.one()
    assert deposit.amount == 500
    assert deposit.source == "dossier jouve [35]"
    assert deposit.userId == beneficiary.id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary == beneficiary
    assert beneficiary.notificationSubscriptions == {"marketing_push": True, "marketing_email": False}

    assert push_testing.requests == [
        {
            "user_id": beneficiary.id,
            "attribute_values": {
                "u.credit": 50000,
                "date(u.date_of_birth)": "1995-02-05T00:00:00",
                "u.postal_code": "35123",
                "date(u.date_created)": beneficiary.dateCreated.strftime("%Y-%m-%dT%H:%M:%S"),
                "u.marketing_push_subscription": True,
                "u.is_beneficiary": True,
                "date(u.deposit_expiration_date)": "2015-05-15T09:00:00",
            },
        }
    ]


@patch(
    "pcapi.settings.JOUVE_APPLICATION_BACKEND",
    "tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend",
)
@pytest.mark.usefixtures("db_session")
def test_cannot_save_beneficiary_if_email_is_already_taken(app):
    # Given
    application_id = 35
    email = "rennes@example.org"
    user = create_user(email=email, idx=4)
    repository.save(user)

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    user = User.query.one()
    assert user.id == 4

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary is None
    assert beneficiary_import.detail == f"Email {email} is already taken."

    assert push_testing.requests == []


@patch(
    "pcapi.settings.JOUVE_APPLICATION_BACKEND",
    "tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend",
)
@pytest.mark.usefixtures("db_session")
def test_cannot_save_beneficiary_if_duplicate(app):
    # Given
    first_name = "Thomas"
    last_name = "DURAND"
    date_of_birth = datetime(1995, 2, 5)
    existing_user_id = 4

    user = create_user(first_name=first_name, last_name=last_name, date_of_birth=date_of_birth, idx=existing_user_id)
    repository.save(user)

    application_id = 35

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    user = User.query.one()
    assert user.id == existing_user_id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary is None
    assert beneficiary_import.detail == f"User with id {existing_user_id} is a duplicate."


@pytest.mark.usefixtures("db_session")
@override_settings(
    JOUVE_APPLICATION_BACKEND="tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend"
)
@override_features(WHOLE_FRANCE_OPENING=False)
def test_cannot_save_beneficiary_if_department_is_not_eligible_legacy_behaviour(app):
    # Given
    application_id = 36
    postal_code = f"{application_id}123"

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    users_count = User.query.count()
    assert users_count == 0

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary is None
    assert beneficiary_import.detail == f"Postal code {postal_code} is not eligible."


@pytest.mark.usefixtures("db_session")
@override_settings(
    JOUVE_APPLICATION_BACKEND="tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend"
)
@override_features(WHOLE_FRANCE_OPENING=True)
def test_cannot_save_beneficiary_if_department_is_not_eligible(app):
    # Given
    application_id = 988
    postal_code = f"{application_id}123"

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    users_count = User.query.count()
    assert users_count == 0

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary is None
    assert beneficiary_import.detail == f"Postal code {postal_code} is not eligible."


@patch("pcapi.use_cases.create_beneficiary_from_application.validate")
@patch("pcapi.use_cases.create_beneficiary_from_application.send_rejection_email_to_beneficiary_pre_subscription")
@patch(
    "pcapi.settings.JOUVE_APPLICATION_BACKEND",
    "tests.use_cases.create_beneficiary_from_application_test.FakeBeneficiaryJouveBackend",
)
@pytest.mark.usefixtures("db_session")
def test_calls_send_rejection_mail_with_validation_error(
    mocked_send_rejection_email_to_beneficiary_pre_subscription, stubed_validate, app
):
    # Given
    application_id = 35
    error = BeneficiaryIsADuplicate("Some reason")
    stubed_validate.side_effect = error
    pre_subscription = BeneficiaryPreSubscription(
        application_id=application_id,
        postal_code=f"{application_id:02d}123",
        **PRE_SUBSCRIPTION_BASE_DATA,
    )

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    mocked_send_rejection_email_to_beneficiary_pre_subscription.assert_called_once_with(
        beneficiary_pre_subscription=pre_subscription,
        beneficiary_is_eligible=True,
    )
