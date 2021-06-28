from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time
import pytest

from pcapi.core.testing import override_features
from pcapi.core.users.models import PhoneValidationStatusType
from pcapi.core.users.models import User
from pcapi.model_creators.generic_creators import create_user
from pcapi.models import BeneficiaryImport
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.models.deposit import Deposit
from pcapi.notifications.push import testing as push_testing
from pcapi.repository import repository

from tests.conftest import TestClient


JOUVE_CONTENT = {
    "activity": "Apprenti",
    "address": "3 rue de Valois",
    "birthDateTxt": "22/05/1995",
    "bodyBirthDateCtrl": "OK",
    "bodyBirthDateLevel": 100,
    "bodyFirstnameCtrl": "OK",
    "bodyFirstnameLevel": 100,
    "bodyNameLevel": 80,
    "bodyNameCtrl": "OK",
    "bodyPieceNumber": "id-piece-number",
    "bodyPieceNumberCtrl": "OK",
    "bodyPieceNumberLevel": 100,
    "city": "Paris",
    "creatorCtrl": "OK",
    "email": "rennes@example.org",
    "gender": "F",
    "id": 35,
    "initialNumberCtrl": "OK",
    "initialSizeCtrl": "OK",
    "firstName": "Thomas",
    "lastName": "DURAND",
    "phoneNumber": "0123456789",
    "postalCode": "35123",
}


class Returns200Test:
    @patch("pcapi.routes.webapp.beneficiaries.beneficiary_job.delay")
    def when_has_exact_payload(self, mocked_beneficiary_job, app):
        # Given
        data = {"id": "5"}

        # When
        response = TestClient(app.test_client()).post("/beneficiaries/application_update", json=data)

        # Then
        assert response.status_code == 200
        mocked_beneficiary_job.assert_called_once_with(5)

    @override_features(APPLY_BOOKING_LIMITS_V2=False)
    @patch("pcapi.use_cases.create_beneficiary_from_application.send_accepted_as_beneficiary_email")
    @patch("pcapi.use_cases.create_beneficiary_from_application.send_activation_email")
    @patch("pcapi.domain.password.random_token")
    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    @freeze_time("2013-05-15 09:00:00")
    @pytest.mark.usefixtures("db_session")
    def test_user_becomes_beneficiary(
        self,
        _get_raw_content,
        stubed_random_token,
        mocked_send_activation_email,
        mocked_send_accepted_as_beneficiary_email,
        app,
    ):
        """
        Test that a user which has validated its email and phone number, becomes a
        beneficiary. And that this user's information is updated with the
        application's.
        """
        # Given
        application_id = 35
        stubed_random_token.return_value = "token"
        _get_raw_content.return_value = JOUVE_CONTENT

        user = create_user(idx=4, email="rennes@example.org", is_beneficiary=False, is_email_validated=True)

        user.phoneValidationStatus = PhoneValidationStatusType.VALIDATED
        repository.save(user)

        # When
        data = {"id": "35"}
        response = TestClient(app.test_client()).post("/beneficiaries/application_update", json=data)

        # Then
        assert response.status_code == 200

        beneficiary = User.query.one()
        assert beneficiary.activity == "Apprenti"
        assert beneficiary.address == "3 rue de Valois"
        assert beneficiary.isBeneficiary is True
        assert beneficiary.city == "Paris"
        assert beneficiary.civility == "Mme"
        assert beneficiary.dateOfBirth == datetime(1995, 5, 22)
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

        # New beneficiary already received the account activation email with
        # the reset password token
        assert not beneficiary.tokens
        mocked_send_activation_email.assert_not_called()
        mocked_send_accepted_as_beneficiary_email.assert_called_once()

        assert push_testing.requests == [
            {
                "user_id": beneficiary.id,
                "attribute_values": {
                    "u.credit": 50000,
                    "u.departement_code": "35",
                    "date(u.date_of_birth)": "1995-05-22T00:00:00",
                    "u.postal_code": "35123",
                    "date(u.date_created)": beneficiary.dateCreated.strftime("%Y-%m-%dT%H:%M:%S"),
                    "u.marketing_push_subscription": True,
                    "u.is_beneficiary": True,
                    "date(u.deposit_expiration_date)": "2015-05-15T09:00:00",
                },
            }
        ]

    @override_features(FORCE_PHONE_VALIDATION=True)
    @patch("pcapi.use_cases.create_beneficiary_from_application.send_accepted_as_beneficiary_email")
    @patch("pcapi.use_cases.create_beneficiary_from_application.send_activation_email")
    @patch("pcapi.domain.password.random_token")
    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    @freeze_time("2013-05-15 09:00:00")
    @pytest.mark.usefixtures("db_session")
    def test_user_does_not_become_beneficiary(
        self,
        _get_raw_content,
        stubed_random_token,
        mocked_send_activation_email,
        mocked_send_accepted_as_beneficiary_email,
        app,
    ):
        """
        Test that an application is correctly processed and that a non-beneficiary
        user is created. It cannot become a beneficiary since validation steps are
        missing.
        """
        # Given
        application_id = 35
        stubed_random_token.return_value = "token"
        _get_raw_content.return_value = JOUVE_CONTENT

        # When
        data = {"id": "35"}
        response = TestClient(app.test_client()).post("/beneficiaries/application_update", json=data)

        # Then
        assert response.status_code == 200

        user = User.query.one()
        assert user.activity == "Apprenti"
        assert user.address == "3 rue de Valois"
        assert not user.isBeneficiary
        assert user.city == "Paris"
        assert user.civility == "Mme"
        assert user.dateOfBirth == datetime(1995, 5, 22)
        assert user.departementCode == "35"
        assert user.email == "rennes@example.org"
        assert user.firstName == "Thomas"
        assert not user.hasSeenTutorials
        assert not user.isAdmin
        assert user.lastName == "DURAND"
        assert user.password is not None
        assert user.phoneNumber == "0123456789"
        assert user.postalCode == "35123"
        assert user.publicName == "Thomas DURAND"
        assert user.notificationSubscriptions == {"marketing_push": True, "marketing_email": True}

        assert not Deposit.query.one_or_none()

        beneficiary_import = BeneficiaryImport.query.one()
        assert beneficiary_import.currentStatus == ImportStatus.CREATED
        assert beneficiary_import.applicationId == application_id
        assert beneficiary_import.beneficiary == user

        assert len(user.tokens) == 1
        mocked_send_activation_email.assert_called_once()
        mocked_send_accepted_as_beneficiary_email.assert_not_called()

        assert push_testing.requests == [
            {
                "user_id": user.id,
                "attribute_values": {
                    "u.credit": 0,
                    "u.departement_code": "35",
                    "date(u.date_of_birth)": "1995-05-22T00:00:00",
                    "u.postal_code": "35123",
                    "date(u.date_created)": user.dateCreated.strftime("%Y-%m-%dT%H:%M:%S"),
                    "u.marketing_push_subscription": True,
                    "u.is_beneficiary": False,
                    "date(u.deposit_expiration_date)": None,
                },
            }
        ]


class Returns400Test:
    @patch("pcapi.routes.webapp.beneficiaries.beneficiary_job.delay")
    def when_no_payload(self, mocked_beneficiary_job, app):
        # When
        response = TestClient(app.test_client()).post("/beneficiaries/application_update")

        # Then
        assert response.status_code == 400
        mocked_beneficiary_job.assert_not_called()

    @patch("pcapi.routes.webapp.beneficiaries.beneficiary_job.delay")
    def when_has_wrong_payload(self, mocked_beneficiary_job, app):
        # Given
        data = {"next-id": "5"}

        # When
        response = TestClient(app.test_client()).post("/beneficiaries/application_update", json=data)

        # Then
        assert response.status_code == 400
        mocked_beneficiary_job.assert_not_called()

    @patch("pcapi.routes.webapp.beneficiaries.beneficiary_job.delay")
    def when_id_is_not_a_number(self, mocked_beneficiary_job, app):
        # Given
        data = {"id": "cinq"}

        # When
        response = TestClient(app.test_client()).post("/beneficiaries/application_update", json=data)

        # Then
        assert response.status_code == 400
        mocked_beneficiary_job.assert_not_called()
