import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
import pytest

import pcapi.core.fraud.api as fraud_api
import pcapi.core.fraud.factories as fraud_factories
import pcapi.core.fraud.models as fraud_models
from pcapi.core.testing import override_features
import pcapi.core.users.factories as users_factories
import pcapi.core.users.models as users_models
from pcapi.models import db


@pytest.mark.usefixtures("db_session")
class JouveFraudCheckTest:
    application_id = 35
    user_email = "tour.de.passpass@example.com"
    AGE18_ELIGIBLE_BIRTH_DATE = datetime.datetime.now() - relativedelta(years=18, months=4)

    JOUVE_CONTENT = {
        "activity": "Etudiant",
        "address": "",
        "birthDateTxt": f"{AGE18_ELIGIBLE_BIRTH_DATE:%d/%m/%Y}",
        "birthLocation": "STRASBOURG I67)",
        "birthLocationCtrl": "OK",
        "bodyBirthDate": "06 06 2002",
        "bodyBirthDateCtrl": "OK",
        "bodyBirthDateLevel": "100",
        "bodyFirstnameCtrl": "OK",
        "bodyFirstnameLevel": "100",
        "bodyName": "DUPO",
        "bodyNameCtrl": "OK",
        "bodyNameLevel": "100",
        "bodyPieceNumber": "140767100016",
        "bodyPieceNumberCtrl": "OK",
        "bodyPieceNumberLevel": "100",
        "city": "",
        "creatorCtrl": "NOT_APPLICABLE",
        "docFileID": 535,
        "docObjectID": 535,
        "email": user_email,
        "firstName": "CHRISTOPHE",
        "gender": "M",
        "id": application_id,
        "initial": "",
        "initialNumberCtrl": "OK",
        "initialSizeCtrl": "OK",
        "lastName": "DUPO",
        "phoneNumber": "",
        "postalCode": "",
        "posteCode": "678083",
        "posteCodeCtrl": "OK",
        "registrationDate": "10/06/2021 21:00",
        "serviceCode": "1",
        "serviceCodeCtrl": "OK",
    }

    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    def test_jouve_update(self, _get_raw_content, client):
        user = users_factories.UserFactory(
            hasCompletedIdCheck=True,
            phoneValidationStatus=users_models.PhoneValidationStatusType.VALIDATED,
            dateOfBirth=self.AGE18_ELIGIBLE_BIRTH_DATE,
            email=self.user_email,
        )
        _get_raw_content.return_value = self.JOUVE_CONTENT

        response = client.post("/beneficiaries/application_update", json={"id": self.application_id})
        assert response.status_code == 200

        fraud_check = fraud_models.BeneficiaryFraudCheck.query.filter_by(
            user=user, type=fraud_models.FraudCheckType.JOUVE
        ).first()
        fraud_result = fraud_models.BeneficiaryFraudResult.query.filter_by(user=user).first()
        jouve_fraud_content = fraud_models.JouveContent(**fraud_check.resultContent)

        assert jouve_fraud_content.bodyPieceNumber == "140767100016"
        assert fraud_check.dateCreated
        assert fraud_check.thirdPartyId == "35"
        assert fraud_result.status == fraud_models.FraudStatus.OK

        db.session.refresh(user)
        assert user.has_beneficiary_role

    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    def test_jouve_update_duplicate_user(self, _get_raw_content, client):
        existing_user = users_factories.BeneficiaryGrant18Factory(
            firstName="Christophe",
            lastName="Dupo",
            dateOfBirth=self.AGE18_ELIGIBLE_BIRTH_DATE,
            idPieceNumber="140767100016",
        )
        user = users_factories.UserFactory(
            hasCompletedIdCheck=True,
            phoneValidationStatus=users_models.PhoneValidationStatusType.VALIDATED,
            dateOfBirth=self.AGE18_ELIGIBLE_BIRTH_DATE,
            email=self.user_email,
        )
        _get_raw_content.return_value = self.JOUVE_CONTENT

        response = client.post("/beneficiaries/application_update", json={"id": self.application_id})
        assert response.status_code == 200

        fraud_result = fraud_models.BeneficiaryFraudResult.query.filter_by(user=user).first()

        assert fraud_result.status == fraud_models.FraudStatus.SUSPICIOUS
        assert (
            fraud_result.reason
            == f"Duplicat de l'utilisateur {existing_user.id} ; Le n° de cni 140767100016 est déjà pris par l'utilisateur {existing_user.id}"
        )

        db.session.refresh(user)
        assert not user.has_beneficiary_role

    @override_features(PAUSE_JOUVE_SUBSCRIPTION=True)
    @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    def test_jouve_subscription_journey_on_hold(self, _get_raw_content, client):
        user = users_factories.UserFactory(
            hasCompletedIdCheck=True,
            phoneValidationStatus=users_models.PhoneValidationStatusType.VALIDATED,
            dateOfBirth=self.AGE18_ELIGIBLE_BIRTH_DATE,
            email=self.user_email,
        )
        _get_raw_content.return_value = self.JOUVE_CONTENT

        response = client.post("/beneficiaries/application_update", json={"id": self.application_id})
        assert response.status_code == 200

        fraud_result = fraud_models.BeneficiaryFraudResult.query.filter_by(user=user).first()

        assert fraud_result.status == fraud_models.FraudStatus.SUBSCRIPTION_ON_HOLD

        db.session.refresh(user)
        assert not user.has_beneficiary_role

    @pytest.mark.parametrize("jouve_field", ["birthLocationCtrl", "bodyBirthDateCtrl", "bodyNameCtrl"])
    @pytest.mark.parametrize("wrong_possible_value", ["NOT_APPLICABLE", "KO"])
    def test_id_check_fraud_items_wrong_values_are_supiscious(self, jouve_field, wrong_possible_value):
        jouve_content = fraud_factories.JouveContentFactory(**{jouve_field: wrong_possible_value})
        item_found = False
        for item in fraud_api._id_check_fraud_items(jouve_content):
            if item.detail == f"Le champ {jouve_field} est {wrong_possible_value}":
                assert item.status == fraud_models.FraudStatus.SUSPICIOUS
                item_found = True

        assert item_found

    @pytest.mark.parametrize(
        "id_piece_number",
        [
            "I III1",
            "I I 1JII 11IB I E",
            "",
            "Passeport n: XXXXX",
        ],
    )
    def test_jouve_id_piece_number_wrong_format(self, id_piece_number):
        item = fraud_api.validate_id_piece_number_format_fraud_item(id_piece_number)
        assert item.status == fraud_models.FraudStatus.SUSPICIOUS

    @pytest.mark.parametrize(
        "id_piece_number",
        [
            "321070751234",
            "090435303687",
            "00000000 0 ZU4",  # portugal format
            "03146310",  # andora CNI format
        ],
    )
    def test_jouve_id_piece_number_valid_format(self, id_piece_number):
        item = fraud_api.validate_id_piece_number_format_fraud_item(id_piece_number)
        assert item.status == fraud_models.FraudStatus.OK

    def test_on_identity_fraud_check_result_retry(self):
        user = users_factories.UserFactory()
        content = fraud_factories.JouveContentFactory(
            birthLocationCtrl="OK",
            bodyBirthDateCtrl="OK",
            bodyBirthDateLevel=100,
            bodyFirstnameCtrl="OK",
            bodyFirstnameLevel=100,
            bodyNameLevel=100,
            bodyNameCtrl="OK",
            bodyPieceNumber="wrong-id-piece-number",
            bodyPieceNumberCtrl="KO",  # ensure we correctly update this field later in the test
            bodyPieceNumberLevel=100,
            creatorCtrl="OK",
            initialSizeCtrl="OK",
        )
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.JOUVE, user=user, resultContent=content
        )
        fraud_check = fraud_api.admin_update_identity_fraud_check_result(user, "123123123123")
        fraud_result = fraud_factories.BeneficiaryFraudResultFactory(
            user=user, status=fraud_models.FraudStatus.SUSPICIOUS, reason="Suspiscious case"
        )
        fraud_api.on_identity_fraud_check_result(user, fraud_check)
        fraud_result = fraud_models.BeneficiaryFraudResult.query.get(fraud_result.id)
        assert fraud_result.status == fraud_models.FraudStatus.OK

    def test_admin_update_identity_fraud_check_result(self):
        user = users_factories.UserFactory()

        fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.JOUVE,
            user=user,
        )

        fraud_check = fraud_api.admin_update_identity_fraud_check_result(user, "id-piece-number")
        content = fraud_models.JouveContent(**fraud_check.resultContent)
        assert content.bodyPieceNumberLevel == 100
        assert content.bodyPieceNumber == "id-piece-number"
        assert content.bodyPieceNumberCtrl == "OK"

    # TODO(xordoquy): make fraud fields configurable and reactivate this test
    # @patch("pcapi.connectors.beneficiaries.jouve_backend._get_raw_content")
    # def test_jouve_update_id_fraud(self, _get_raw_content, client):

    #     user = users_factories.users_factories.UserFactory(
    #         hasCompletedIdCheck=True,
    #         phoneValidationStatus=PhoneValidationStatusType.VALIDATED,
    #         dateOfBirth=datetime(2002, 6, 8),
    #         email=self.user_email,
    #     )
    #     _get_raw_content.return_value = self.JOUVE_CONTENT | {"serviceCodeCtrl": "KO", "bodyFirstnameLevel": "30"}

    #     response = client.post("/beneficiaries/application_update", json={"id": self.application_id})
    #     assert response.status_code == 200

    #     fraud_result = fraud_models.BeneficiaryFraudResult.query.filter_by(user=user).first()

    #     assert fraud_result.status == fraud_models.FraudStatus.KO
    #     assert (
    #         fraud_result.reason
    #         == "Le champ serviceCodeCtrl est KO ; Le champ bodyFirstnameLevel a le score 30 (minimum 50)"
    #     )

    #     db.session.refresh(user)
    #     assert not user.has_beneficiary_role


@pytest.mark.usefixtures("db_session")
class CommonTest:
    def test_validator_data(self):
        user = users_factories.UserFactory()
        fraud_data = fraud_factories.BeneficiaryFraudCheckFactory(user=user, type=fraud_models.FraudCheckType.JOUVE)
        fraud_factories.BeneficiaryFraudCheckFactory(user=user, type=fraud_models.FraudCheckType.DMS)

        expected = fraud_api.get_source_data(user)

        assert isinstance(expected, fraud_models.JouveContent)
        assert expected == fraud_models.JouveContent(**fraud_data.resultContent)


@pytest.mark.usefixtures("db_session")
class UpsertFraudResultTest:
    def test_create_on_first_fraud_result(self):
        user = users_factories.UserFactory()
        assert fraud_models.BeneficiaryFraudResult.query.count() == 0

        result = fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, "no reason at all")

        assert fraud_models.BeneficiaryFraudResult.query.count() == 1
        assert result.user == user
        assert result.reason == "no reason at all"

    def test_update_on_following_fraud_results(self):
        user = users_factories.UserFactory()
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.OK)
        assert fraud_models.BeneficiaryFraudResult.query.count() == 1

        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, "no reason at all")
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.KO, "no reason at all")

        assert fraud_models.BeneficiaryFraudResult.query.count() == 1

    @pytest.mark.parametrize("fraud_status", (fraud_models.FraudStatus.SUSPICIOUS, fraud_models.FraudStatus.KO))
    def test_reason_is_mandatory_when_not_ok(self, fraud_status):
        user = users_factories.UserFactory()

        with pytest.raises(ValueError) as excinfo:
            fraud_api.upsert_fraud_result(user, fraud_status)

        assert str(excinfo.value) == f"a reason should be provided when setting fraud result to {fraud_status.value}"

    def test_do_not_repeat_previous_reason_and_keep_history(self):
        """
        Test that the upsert function does updated the reason when consecutive
        calls do not use the same reason.
        """
        user = users_factories.UserFactory()
        first_reason = "first reason"
        second_reason = "second reason"

        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, first_reason)
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, first_reason)
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, first_reason)
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, second_reason)
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, second_reason)
        fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, first_reason)
        result = fraud_api.upsert_fraud_result(user, fraud_models.FraudStatus.SUSPICIOUS, first_reason)

        assert fraud_models.BeneficiaryFraudResult.query.count() == 1
        assert result.user == user
        assert result.reason == f"{first_reason} ; {second_reason} ; {first_reason}"


@pytest.mark.usefixtures("db_session")
class CommonFraudCheckTest:
    def test_duplicate_id_piece_number_ok(self):
        fraud_item = fraud_api._duplicate_id_piece_number_fraud_item("random_id")
        assert fraud_item.status == fraud_models.FraudStatus.OK

    def test_duplicate_id_piece_number_suspicious(self):
        user = users_factories.BeneficiaryGrant18Factory()

        fraud_item = fraud_api._duplicate_id_piece_number_fraud_item(user.idPieceNumber)
        assert fraud_item.status == fraud_models.FraudStatus.SUSPICIOUS

    def test_duplicate_user_fraud_ok(self):
        fraud_item = fraud_api._duplicate_user_fraud_item(
            first_name="Jean", last_name="Michel", birth_date=datetime.date.today()
        )

        assert fraud_item.status == fraud_models.FraudStatus.OK

    def test_duplicate_user_fraud_suspicious(self):
        user = users_factories.BeneficiaryGrant18Factory()
        fraud_item = fraud_api._duplicate_user_fraud_item(
            first_name=user.firstName, last_name=user.lastName, birth_date=user.dateOfBirth.date()
        )

        assert fraud_item.status == fraud_models.FraudStatus.SUSPICIOUS

    @pytest.mark.parametrize(
        "fraud_check_type",
        [fraud_models.FraudCheckType.DMS, fraud_models.FraudCheckType.JOUVE],
    )
    def test_user_validation_is_beneficiary(self, fraud_check_type):
        user = users_factories.BeneficiaryGrant18Factory()
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(type=fraud_check_type, user=user)
        fraud_result = fraud_api.on_identity_fraud_check_result(user, fraud_check)

        assert (
            "L’utilisateur est déjà bénéfiaire, avec un portefeuille non expiré. Il ne peut pas prétendre au pass culture 18 ans"
            in fraud_result.reason
        )
        assert fraud_result.status == fraud_models.FraudStatus.KO

    @pytest.mark.parametrize(
        "age",
        [15, 16, 17],
    )
    def test_underage_user_validation_is_beneficiary(self, age):
        user = users_factories.UnderageBeneficiaryFactory()
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            user=user,
            resultContent=fraud_factories.EduconnectContentFactory(age=age),
        )
        fraud_result = fraud_api.on_identity_fraud_check_result(user, fraud_check)

        assert (
            "L’utilisateur est déjà bénéfiaire, avec un portefeuille non expiré. Il ne peut pas prétendre au pass culture 15-17 ans"
            in fraud_result.reason
        )
        assert fraud_result.status == fraud_models.FraudStatus.KO

    @pytest.mark.parametrize(
        "fraud_check_type",
        [fraud_models.FraudCheckType.DMS, fraud_models.FraudCheckType.JOUVE],
    )
    def test_user_validation_has_email_validated(self, fraud_check_type):
        user = users_factories.UserFactory(isEmailValidated=False)
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(type=fraud_check_type, user=user)
        fraud_result = fraud_api.on_identity_fraud_check_result(user, fraud_check)

        assert "L'email de l'utilisateur n'est pas validé" in fraud_result.reason
        assert fraud_result.status == fraud_models.FraudStatus.KO

    @pytest.mark.parametrize("age", [15, 16, 17])
    def test_underage_user_validation_has_email_validated(self, age):
        user = users_factories.UserFactory(isEmailValidated=False)
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            user=user,
            resultContent=fraud_factories.EduconnectContentFactory(age=age),
        )
        fraud_result = fraud_api.on_identity_fraud_check_result(user, fraud_check)

        assert "L'email de l'utilisateur n'est pas validé" in fraud_result.reason
        assert fraud_result.status == fraud_models.FraudStatus.KO

    @override_features(FORCE_PHONE_VALIDATION=True)
    @pytest.mark.parametrize(
        "phone_status",
        [
            users_models.PhoneValidationStatusType.BLOCKED_TOO_MANY_CODE_SENDINGS,
            users_models.PhoneValidationStatusType.BLOCKED_TOO_MANY_CODE_VERIFICATION_TRIES,
        ],
    )
    @pytest.mark.parametrize("fraud_check_type", [fraud_models.FraudCheckType.DMS, fraud_models.FraudCheckType.JOUVE])
    def test_user_validation_has_phone_validated(self, phone_status, fraud_check_type):
        user = users_factories.UserFactory(
            isEmailValidated=True,
            phoneValidationStatus=phone_status,
        )
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(type=fraud_check_type, user=user)
        fraud_result = fraud_api.on_identity_fraud_check_result(user, fraud_check)

        assert "Le n° de téléphone de l'utilisateur n'est pas validé" in fraud_result.reason
        assert fraud_result.status == fraud_models.FraudStatus.KO

    @pytest.mark.parametrize("fraud_check_type", [fraud_models.FraudCheckType.DMS, fraud_models.FraudCheckType.JOUVE])
    def test_previously_validated_user_with_retry(self, fraud_check_type):
        # The user is already beneficiary, and has already done all the checks but
        # for any circumstances, someone is trying to redo the validation
        user = users_factories.BeneficiaryGrant18Factory()
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(type=fraud_check_type, user=user)
        fraud_result = fraud_factories.BeneficiaryFraudResultFactory(user=user, status=fraud_models.FraudStatus.OK)

        fraud_api.on_identity_fraud_check_result(user, fraud_check)

        assert fraud_result.status == fraud_models.FraudStatus.OK


@pytest.mark.usefixtures("db_session")
class DMSFraudCheckTest:
    def test_dms_fraud_check(self):
        user = users_factories.UserFactory()
        content = fraud_factories.DMSContentFactory()
        fraud_api.on_dms_fraud_check(user, content)

        fraud_check = fraud_models.BeneficiaryFraudCheck.query.filter_by(
            user=user, type=fraud_models.FraudCheckType.DMS
        ).one_or_none()

        expected_content = fraud_models.DMSContent(**fraud_check.resultContent)
        assert content == expected_content

        fraud_result = fraud_models.BeneficiaryFraudResult.query.filter_by(user=user).one_or_none()
        assert fraud_result.status == fraud_models.FraudStatus.OK

    def test_admin_update_identity_fraud_check_result(self):
        user = users_factories.UserFactory()

        fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.DMS,
            user=user,
        )

        fraud_check = fraud_api.admin_update_identity_fraud_check_result(user, "id-piece-number")
        content = fraud_models.DMSContent(**fraud_check.resultContent)
        assert content.id_piece_number == "id-piece-number"


@pytest.mark.usefixtures("db_session")
class UserFraudsterTest:
    @pytest.mark.parametrize(
        "fraud_status,is_fraudster",
        (
            (fraud_models.FraudStatus.OK, False),
            (fraud_models.FraudStatus.KO, True),
            (fraud_models.FraudStatus.SUSPICIOUS, True),
        ),
    )
    def test_is_user_fraudster(self, fraud_status, is_fraudster):
        fraud_result = fraud_factories.BeneficiaryFraudResultFactory(status=fraud_status)
        assert is_fraudster == fraud_api.is_user_fraudster(fraud_result.user)


@pytest.mark.usefixtures("db_session")
class EduconnectFraudTest:
    def test_on_educonnect_result(self):
        fraud_factories.IneHashWhitelistFactory(ine_hash="5ba682c0fc6a05edf07cd8ed0219258f")
        user = users_factories.UserFactory()
        birth_date = (datetime.datetime.today() - relativedelta(years=15)).date()
        fraud_api.on_educonnect_result(
            user,
            fraud_models.EduconnectContent(
                birth_date=birth_date,
                educonnect_id="id-1",
                first_name="Lucy",
                ine_hash="5ba682c0fc6a05edf07cd8ed0219258f",
                last_name="Ellingson",
            ),
        )

        fraud_check = fraud_models.BeneficiaryFraudCheck.query.filter_by(
            user=user, type=fraud_models.FraudCheckType.EDUCONNECT
        ).one_or_none()
        assert fraud_check is not None
        assert fraud_check.userId == user.id
        assert fraud_check.type == fraud_models.FraudCheckType.EDUCONNECT
        assert fraud_check.source_data().__dict__ == {
            "educonnect_id": "id-1",
            "first_name": "Lucy",
            "ine_hash": "5ba682c0fc6a05edf07cd8ed0219258f",
            "last_name": "Ellingson",
            "birth_date": birth_date,
        }
        assert user.beneficiaryFraudResult.status == fraud_models.FraudStatus.OK

    @pytest.mark.parametrize("age", [14, 18])
    def test_age_fraud_check_ko(self, age):
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            resultContent=fraud_factories.EduconnectContentFactory(age=age),
        )
        result = fraud_api.educonnect_fraud_checks(beneficiary_fraud_check=fraud_check)

        age_check = next(
            fraud_check
            for fraud_check in result
            if fraud_check.reason_code == fraud_models.FraudReasonCode.AGE_NOT_VALID
        )
        assert age_check.status == fraud_models.FraudStatus.KO
        assert (
            age_check.detail == f"L'age de l'utilisateur est invalide ({age} ans). Il devrait être parmi [15, 16, 17]"
        )

    @pytest.mark.parametrize("age", [15, 16, 17])
    def test_age_fraud_check_ok(self, age):
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            resultContent=fraud_factories.EduconnectContentFactory(age=age),
        )
        result = fraud_api.educonnect_fraud_checks(beneficiary_fraud_check=fraud_check)

        age_check = next(
            (
                fraud_check
                for fraud_check in result
                if fraud_check.reason_code == fraud_models.FraudReasonCode.AGE_NOT_VALID
            ),
            None,
        )
        assert not age_check

    @override_features(ENABLE_NATIVE_EAC_INDIVIDUAL=True)
    def test_duplicates_fraud_checks(self):
        already_existing_user = users_factories.UnderageBeneficiaryFactory(subscription_age=15)
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            resultContent=fraud_factories.EduconnectContentFactory(
                first_name=already_existing_user.firstName,
                last_name=already_existing_user.lastName,
                birth_date=already_existing_user.dateOfBirth,
            ),
        )
        result = fraud_api.educonnect_fraud_checks(fraud_check)

        duplicate_check = next(
            fraud_check
            for fraud_check in result
            if fraud_check.reason_code == fraud_models.FraudReasonCode.DUPLICATE_USER
        )

        assert duplicate_check.status == fraud_models.FraudStatus.SUSPICIOUS
        assert duplicate_check.detail == f"Duplicat de l'utilisateur {already_existing_user.id}"

    @override_features(ENABLE_NATIVE_EAC_INDIVIDUAL=True)
    def test_ine_duplicates_fraud_checks(self):
        fraud_factories.IneHashWhitelistFactory(ine_hash="ylwavk71o3jiwyla83fxk5pcmmu0ws01")
        same_ine_user = users_factories.UnderageBeneficiaryFactory(ineHash="ylwavk71o3jiwyla83fxk5pcmmu0ws01")
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            resultContent=fraud_factories.EduconnectContentFactory(ine_hash=same_ine_user.ineHash),
        )
        result = fraud_api.educonnect_fraud_checks(fraud_check)

        duplicate_ine_check = next(
            fraud_check
            for fraud_check in result
            if fraud_check.reason_code == fraud_models.FraudReasonCode.DUPLICATE_INE
        )
        assert duplicate_ine_check.status == fraud_models.FraudStatus.SUSPICIOUS
        assert (
            duplicate_ine_check.detail
            == f"L'INE ylwavk71o3jiwyla83fxk5pcmmu0ws01 est déjà pris par l'utilisateur {same_ine_user.id}"
        )

    @override_features(ENABLE_NATIVE_EAC_INDIVIDUAL=True)
    def test_ine_whitelisted_fraud_checks_pass(self):
        fraud_factories.IneHashWhitelistFactory(ine_hash="identifiantWhitelisté1")
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            resultContent=fraud_factories.EduconnectContentFactory(ine_hash="identifiantWhitelisté1"),
        )
        result = fraud_api.educonnect_fraud_checks(fraud_check)

        duplicate_ine_check = next(
            (
                fraud_check
                for fraud_check in result
                if fraud_check.reason_code == fraud_models.FraudReasonCode.INE_NOT_WHITELISTED
            ),
            None,
        )
        assert duplicate_ine_check is None

    @override_features(ENABLE_NATIVE_EAC_INDIVIDUAL=True)
    def test_ine_whitelisted_fraud_checks_fail(self):
        fraud_factories.IneHashWhitelistFactory(ine_hash="identifiantWhitelisté1")
        fraud_check = fraud_factories.BeneficiaryFraudCheckFactory(
            type=fraud_models.FraudCheckType.EDUCONNECT,
            resultContent=fraud_factories.EduconnectContentFactory(ine_hash="identifiantWhitelisté2"),
        )
        result = fraud_api.educonnect_fraud_checks(fraud_check)

        duplicate_ine_check = next(
            fraud_check
            for fraud_check in result
            if fraud_check.reason_code == fraud_models.FraudReasonCode.INE_NOT_WHITELISTED
        )
        assert duplicate_ine_check.status == fraud_models.FraudStatus.SUSPICIOUS
