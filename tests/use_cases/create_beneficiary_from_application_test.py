from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
import pytest

from pcapi.connectors.beneficiaries import jouve_backend
import pcapi.core.mails.testing as mails_testing
from pcapi.core.testing import override_features
from pcapi.core.users import api as users_api
from pcapi.core.users import factories as users_factories
from pcapi.core.users.factories import UserFactory
from pcapi.core.users.models import User
from pcapi.domain.beneficiary_pre_subscription.exceptions import BeneficiaryIsADuplicate
from pcapi.models import BeneficiaryImport
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.models.db import db
from pcapi.models.deposit import Deposit
from pcapi.notifications.push import testing as push_testing
from pcapi.use_cases.create_beneficiary_from_application import create_beneficiary_from_application


APPLICATION_ID = 35

JOUVE_CONTENT = {
    "activity": "Apprenti",
    "address": "3 rue de Valois",
    "birthDateTxt": "22/05/1995",
    "birthLocationCtrl": "OK",
    "bodyBirthDateCtrl": "OK",
    "bodyBirthDateLevel": 100,
    "bodyFirstnameCtrl": "OK",
    "bodyFirstnameLevel": 100,
    "bodyNameLevel": 80,
    "bodyNameCtrl": "OK",
    "bodyPieceNumber": "140767100016",
    "bodyPieceNumberCtrl": "OK",
    "bodyPieceNumberLevel": 100,
    "city": "Paris",
    "creatorCtrl": "OK",
    "email": "rennes@example.org",
    "gender": "F",
    "id": APPLICATION_ID,
    "initialNumberCtrl": "OK",
    "initialSizeCtrl": "OK",
    "firstName": "Thomas",
    "lastName": "DURAND",
    "phoneNumber": "0123456789",
    "postalCode": "35123",
}


@override_features(FORCE_PHONE_VALIDATION=False)
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content", return_value=JOUVE_CONTENT)
@patch("pcapi.domain.password.random_token")
@freeze_time("2013-05-15 09:00:00")
@pytest.mark.usefixtures("db_session")
def test_saved_a_beneficiary_from_application(stubed_random_token, app):
    # Given
    stubed_random_token.return_value = "token"
    users_factories.UserFactory(
        firstName=JOUVE_CONTENT["firstName"], lastName=JOUVE_CONTENT["lastName"], email=JOUVE_CONTENT["email"]
    )
    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
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
    assert deposit.amount == 300
    assert deposit.source == "dossier jouve [35]"
    assert deposit.userId == beneficiary.id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.beneficiary == beneficiary

    assert len(mails_testing.outbox) == 1

    assert len(push_testing.requests) == 1


@override_features(FORCE_PHONE_VALIDATION=False)
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content", return_value=JOUVE_CONTENT)
@freeze_time("2013-05-15 09:00:00")
@pytest.mark.usefixtures("db_session")
def test_application_for_native_app_user(app):
    # Given
    users_api.create_account(
        email=JOUVE_CONTENT["email"],
        password="123456789",
        birthdate=datetime(1995, 4, 15),
        is_email_validated=True,
        send_activation_mail=False,
        marketing_email_subscription=False,
        phone_number="0607080900",
    )
    push_testing.reset_requests()

    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
    beneficiary = User.query.one()

    # the fake Jouve backend returns a default phone number. Since a User
    # alredy exists, the phone number should not be updated during the import process
    assert beneficiary.phoneNumber == "0607080900"

    deposit = Deposit.query.one()
    assert deposit.amount == 300
    assert deposit.source == "dossier jouve [35]"
    assert deposit.userId == beneficiary.id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.beneficiary == beneficiary
    assert beneficiary.notificationSubscriptions == {"marketing_push": True, "marketing_email": False}

    assert len(push_testing.requests) == 1


@freeze_time("2013-05-15 09:00:00")
@override_features(FORCE_PHONE_VALIDATION=False)
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
def test_application_for_native_app_user_with_load_smoothing(_get_raw_content, app, db_session):
    # Given
    application_id = 35
    user = UserFactory(
        dateOfBirth=datetime(2003, 10, 25),
        phoneNumber="0607080900",
        isBeneficiary=False,
        address="an address",
        city="Nantes",
        postalCode="44300",
        activity="Apprenti",
        hasCompletedIdCheck=True,
    )
    push_testing.reset_requests()
    _get_raw_content.return_value = JOUVE_CONTENT | {
        "id": BASE_APPLICATION_ID,
        "firstName": "first_name",
        "lastName": "last_name",
        "email": user.email,
        "activity": "Étudiant",
        "address": "",
        "city": "",
        "gender": "M",
        "bodyPieceNumber": "140767100016",
        "birthDateTxt": "25/10/2003",
        "postalCode": "",
        "phoneNumber": "0102030405",
        "posteCodeCtrl": "OK",
        "serviceCodeCtrl": "OK",
        "birthLocationCtrl": "OK",
        "creatorCtrl": "OK",
        "bodyBirthDateLevel": "100",
        "bodyNameLevel": "100",
    }

    # When
    create_beneficiary_from_application.execute(application_id)

    # Then
    beneficiary = User.query.one()

    # the fake Jouve backend returns a default phone number. Since a User
    # alredy exists, the phone number should not be updated during the import process
    assert beneficiary.phoneNumber == "0607080900"
    assert beneficiary.address == "an address"
    assert beneficiary.activity == "Apprenti"
    assert beneficiary.postalCode == "44300"

    deposit = Deposit.query.one()
    assert deposit.amount == 300
    assert deposit.source == "dossier jouve [35]"
    assert deposit.userId == beneficiary.id

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert beneficiary_import.applicationId == application_id
    assert beneficiary_import.beneficiary == beneficiary
    assert beneficiary.notificationSubscriptions == {"marketing_push": True, "marketing_email": True}

    assert len(push_testing.requests) == 1
    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2016025


@override_features(FORCE_PHONE_VALIDATION=False)
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content", return_value=JOUVE_CONTENT)
@pytest.mark.usefixtures("db_session")
def test_cannot_save_beneficiary_if_email_is_already_taken(app):
    # Given
    email = "rennes@example.org"
    users_factories.BeneficiaryFactory(email=email, id=4)

    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
    user = User.query.one()
    assert user.id == 4

    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.beneficiary == user
    assert beneficiary_import.detail == f"Email {email} is already taken."

    assert push_testing.requests == []


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content", return_value=JOUVE_CONTENT)
@pytest.mark.usefixtures("db_session")
def test_cannot_save_beneficiary_if_duplicate(app):
    # Given
    first_name = "Thomas"
    last_name = "DURAND"
    date_of_birth = datetime(1995, 5, 22)

    applicant = users_factories.UserFactory(
        firstName=JOUVE_CONTENT["firstName"], lastName=JOUVE_CONTENT["lastName"], email=JOUVE_CONTENT["email"]
    )

    existing_user = users_factories.BeneficiaryFactory(
        firstName=first_name, lastName=last_name, dateOfBirth=date_of_birth
    )

    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.detail == f"User with id {existing_user.id} is a duplicate."
    assert beneficiary_import.beneficiary is applicant


@pytest.mark.usefixtures("db_session")
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@override_features(WHOLE_FRANCE_OPENING=False)
def test_cannot_save_beneficiary_if_department_is_not_eligible_legacy_behaviour(get_application_content, app):
    # Given
    postal_code = "75000"
    get_application_content.return_value = JOUVE_CONTENT | {"postalCode": postal_code}
    applicant = users_factories.UserFactory(
        firstName=JOUVE_CONTENT["firstName"], lastName=JOUVE_CONTENT["lastName"], email=JOUVE_CONTENT["email"]
    )

    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.beneficiary == applicant
    assert beneficiary_import.detail == f"Postal code {postal_code} is not eligible."


@pytest.mark.usefixtures("db_session")
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@override_features(WHOLE_FRANCE_OPENING=True)
def test_cannot_save_beneficiary_if_department_is_not_eligible(get_application_content, app):
    # Given
    postal_code = "984"
    get_application_content.return_value = JOUVE_CONTENT | {"postalCode": postal_code}
    applicant = users_factories.UserFactory(
        firstName=JOUVE_CONTENT["firstName"], lastName=JOUVE_CONTENT["lastName"], email=JOUVE_CONTENT["email"]
    )

    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.beneficiary == applicant
    assert beneficiary_import.detail == f"Postal code {postal_code} is not eligible."


@patch("pcapi.use_cases.create_beneficiary_from_application.validate")
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.usefixtures("db_session")
def test_calls_send_rejection_mail_with_validation_error(_get_raw_content, stubed_validate, app):
    # Given
    error = BeneficiaryIsADuplicate("Some reason")
    stubed_validate.side_effect = error
    _get_raw_content.return_value = JOUVE_CONTENT
    users_factories.UserFactory(
        firstName=JOUVE_CONTENT["firstName"], lastName=JOUVE_CONTENT["lastName"], email=JOUVE_CONTENT["email"]
    )

    # When
    create_beneficiary_from_application.execute(APPLICATION_ID)

    # Then
    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 1530996
    assert mails_testing.outbox[0].sent_data["To"] == "rennes@example.org"


@pytest.mark.usefixtures("db_session")
@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
def test_user_pre_creation_is_required(_get_raw_content):
    _get_raw_content.return_value = JOUVE_CONTENT

    create_beneficiary_from_application.execute(APPLICATION_ID)
    beneficiary_import = BeneficiaryImport.query.one()
    assert beneficiary_import.currentStatus == ImportStatus.ERROR
    assert beneficiary_import.applicationId == APPLICATION_ID
    assert beneficiary_import.beneficiary is None
    assert beneficiary_import.statuses[-1].detail == f"Aucun utilisateur trouvé pour l'email {JOUVE_CONTENT['email']}"


BASE_APPLICATION_ID = 35
BASE_JOUVE_CONTENT = {
    "id": BASE_APPLICATION_ID,
    "firstName": "first_name",
    "lastName": "last_name",
    "email": "some@email.com",
    "activity": "some activity",
    "address": "some address",
    "city": "some city",
    "gender": "M",
    "bodyPieceNumber": "id-piece-number",
    "birthDateTxt": "25/10/2003",
    "bodyBirthDateCtrl": "OK",
    "bodyPieceNumberCtrl": "OK",
    "bodyPieceNumberLevel": "100",
    "bodyNameCtrl": "OK",
    "phoneNumber": "+33607080900",
    "postalCode": "77100",
    "posteCodeCtrl": "OK",
    "serviceCodeCtrl": "OK",
    "birthLocationCtrl": "OK",
    "creatorCtrl": "OK",
    "bodyBirthDateLevel": "100",
    "bodyNameLevel": "100",
}


# TODO(xordoquy): make fraud fields configurable and reactivate this test
# @pytest.mark.parametrize(
#     "fraud_strict_detection_parameter",
#     [{"serviceCodeCtrl": "KO"}, {"posteCodeCtrl": "KO"}, {"birthLocationCtrl": "KO"}],
# )
# @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
# @pytest.mark.usefixtures("db_session")
# def test_cannot_save_beneficiary_when_fraud_is_detected(
#     mocked_get_content,
#     fraud_strict_detection_parameter,
#     app,
# ):
#     # Given
#     mocked_get_content.return_value = BASE_JOUVE_CONTENT | {
#         "bodyNameLevel": 30,
#     }
#     # updates mocked return value from parametrized test
#     mocked_get_content.return_value.update(fraud_strict_detection_parameter)

#     # When
#     create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

#     # Then
#     fraud_strict_detection_cause = list(fraud_strict_detection_parameter.keys())[0]
#     beneficiary_import = BeneficiaryImport.query.one()
#     assert beneficiary_import.currentStatus == ImportStatus.REJECTED
#     assert beneficiary_import.detail == f"Fraud controls triggered: {fraud_strict_detection_cause}, bodyNameLevel"

#     assert len(mails_testing.outbox) == 0


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.usefixtures("db_session")
def test_doesnt_save_beneficiary_when_suspicious(
    mocked_get_content,
    app,
):
    # Given
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyBirthDateLevel": "20"}
    users_factories.UserFactory(
        firstName=BASE_JOUVE_CONTENT["firstName"],
        lastName=BASE_JOUVE_CONTENT["lastName"],
        email=BASE_JOUVE_CONTENT["email"],
    )

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    # Then
    assert BeneficiaryImport.query.count() == 0

    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_no_duplicate(
    mocked_get_content,
    app,
):
    # Given
    ID_PIECE_NUMBER = "140767100016"
    subscribing_user = UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
        idPieceNumber=None,
    )
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyPieceNumber": ID_PIECE_NUMBER}

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    # Then
    beneficiary_import = BeneficiaryImport.query.filter(BeneficiaryImport.beneficiary == subscribing_user).first()
    assert beneficiary_import.currentStatus == ImportStatus.CREATED

    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2016025

    db.session.refresh(subscribing_user)
    assert subscribing_user.idPieceNumber == ID_PIECE_NUMBER


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_duplicate(
    mocked_get_content,
    app,
):
    # Given
    ID_PIECE_NUMBER = "140767100016"
    subscribing_user = UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
    )
    UserFactory(idPieceNumber=ID_PIECE_NUMBER)
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyPieceNumber": ID_PIECE_NUMBER}

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    # Then
    beneficiary_import = BeneficiaryImport.query.filter(BeneficiaryImport.beneficiary == subscribing_user).first()
    assert beneficiary_import.currentStatus == ImportStatus.REJECTED
    assert beneficiary_import.detail == f"Fraud controls triggered: id piece number n°{ID_PIECE_NUMBER} already taken"
    assert not subscribing_user.isBeneficiary

    assert len(mails_testing.outbox) == 0


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_invalid_format_avoid_duplicate(
    mocked_get_content,
    app,
):
    # Given
    ID_PIECE_NUMBER = "140767100016"
    UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
    )
    UserFactory(idPieceNumber=ID_PIECE_NUMBER)
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {
        "bodyPieceNumber": ID_PIECE_NUMBER,
        "bodyPieceNumberCtrl": "KO",
    }

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960
    assert mails_testing.outbox[0].sent_data["Mj-campaign"] == "dossier-en-analyse"


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.parametrize("wrong_piece_number", ["NOT_APPLICABLE", "KO", ""])
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_invalid(mocked_get_content, wrong_piece_number):
    subscribing_user = UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
    )
    UserFactory(idPieceNumber=wrong_piece_number)
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyPieceNumberCtrl": wrong_piece_number}

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    # Then
    assert len(subscribing_user.beneficiaryImports) == 0

    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960
    assert mails_testing.outbox[0].sent_data["Mj-campaign"] == "dossier-en-analyse"


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.parametrize("wrong_piece_number", ["NOT_APPLICABLE", "KO", ""])
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_wrong_return_control(mocked_get_content, wrong_piece_number):
    subscribing_user = UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
    )
    UserFactory(idPieceNumber=wrong_piece_number)
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyPieceNumberCtrl": wrong_piece_number}

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    # Then
    assert len(subscribing_user.beneficiaryImports) == 0

    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960
    assert mails_testing.outbox[0].sent_data["Mj-campaign"] == "dossier-en-analyse"


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.parametrize(
    "id_piece_number",
    [
        "I III1",
        "I I 1JII 11IB I E",
        "",
    ],
)
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_wrong_format(mocked_get_content, id_piece_number):
    subscribing_user = UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
    )
    UserFactory(idPieceNumber=id_piece_number)
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyPieceNumber": id_piece_number}

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)

    # Then
    assert len(subscribing_user.beneficiaryImports) == 0

    assert len(mails_testing.outbox) == 1
    assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960
    assert mails_testing.outbox[0].sent_data["Mj-campaign"] == "dossier-en-analyse"


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
@pytest.mark.usefixtures("db_session")
def test_id_piece_number_by_pass(
    mocked_get_content,
    app,
):
    # Given
    ID_PIECE_NUMBER = "NOT_APPLICABLE"
    subscribing_user = UserFactory(
        isBeneficiary=False,
        dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
        email=BASE_JOUVE_CONTENT["email"],
    )
    UserFactory(idPieceNumber=ID_PIECE_NUMBER)
    UserFactory(idPieceNumber=None)
    mocked_get_content.return_value = BASE_JOUVE_CONTENT | {"bodyPieceNumber": ID_PIECE_NUMBER}

    # When
    create_beneficiary_from_application.execute(BASE_APPLICATION_ID, ignore_id_piece_number_field=True)

    # Then
    beneficiary_import = BeneficiaryImport.query.filter(BeneficiaryImport.beneficiary == subscribing_user).first()

    assert beneficiary_import.currentStatus == ImportStatus.CREATED
    assert subscribing_user.isBeneficiary
    assert not subscribing_user.idPieceNumber

    assert len(mails_testing.outbox) == 1


@patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
def test_jouve_raise_403(mocked_get_content, caplog):
    mocked_get_content.side_effect = jouve_backend.ApiJouveException(
        "Error getting API Jouve authentication token", route="/any/url/", status_code=403
    )

    create_beneficiary_from_application.execute(BASE_APPLICATION_ID)
    mocked_get_content.assert_called()
    assert caplog.messages[0] == "Error getting API Jouve authentication token"


@pytest.mark.usefixtures("db_session")
class JouveDataValidationTest:
    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    @pytest.mark.parametrize(
        "jouve_field", ["birthLocationCtrl", "bodyBirthDateCtrl", "bodyNameCtrl", "bodyPieceNumberCtrl"]
    )
    @pytest.mark.parametrize("possible_value", ["KO", "NOT_APPLICABLE", "", "bodyPieceNumberCtrl"])
    def test_mandatory_jouve_fields_wrong_data(self, mocked_get_content, jouve_field, possible_value):
        UserFactory(
            isBeneficiary=False,
            dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
            email=BASE_JOUVE_CONTENT["email"],
        )
        mocked_get_content.return_value = BASE_JOUVE_CONTENT | {jouve_field: possible_value}
        create_beneficiary_from_application.execute(BASE_APPLICATION_ID, ignore_id_piece_number_field=True)

        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960
        assert mails_testing.outbox[0].sent_data["Mj-campaign"] == "dossier-en-analyse"

    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    @pytest.mark.parametrize("jouve_field", ["bodyBirthDateLevel", "bodyNameLevel", "bodyPieceNumberLevel"])
    @pytest.mark.parametrize("possible_value", ["", "NOT_APPLICABLE", "25"])
    def test_mandatory_jouve_fields_wrong_integer_data(self, mocked_get_content, jouve_field, possible_value):
        UserFactory(
            isBeneficiary=False,
            dateOfBirth=datetime.now() - relativedelta(years=18, day=5),
            email=BASE_JOUVE_CONTENT["email"],
        )
        mocked_get_content.return_value = BASE_JOUVE_CONTENT | {jouve_field: possible_value}
        create_beneficiary_from_application.execute(BASE_APPLICATION_ID, ignore_id_piece_number_field=True)

        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["Mj-TemplateID"] == 2905960
        assert mails_testing.outbox[0].sent_data["Mj-campaign"] == "dossier-en-analyse"
