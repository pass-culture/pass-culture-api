import pytest

from pcapi.core.users.factories import UserFactory
from pcapi.core.users.models import User
from pcapi.model_creators.generic_creators import create_user
from pcapi.repository import repository
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


class Patch:
    class Returns200:
        @pytest.mark.usefixtures("db_session")
        def when_changes_are_allowed(self, app):
            # given
            user = UserFactory()
            user_id = user.id
            data = {
                "publicName": "Anne",
                "email": "new@example.com",
                "postalCode": "93020",
                "phoneNumber": "1234567890",
                "departementCode": "97",
                "hasSeenTutorials": True,
            }

            # when
            response = (
                TestClient(app.test_client()).with_auth(email=user.email).patch("/beneficiaries/current", json=data)
            )

            # then
            user = User.query.get(user_id)
            assert response.status_code == 200
            assert response.json["id"] == humanize(user.id)
            assert response.json["publicName"] == user.publicName
            assert user.publicName == data["publicName"]
            assert response.json["email"] == user.email
            assert user.email == data["email"]
            assert response.json["postalCode"] == user.postalCode
            assert user.postalCode == data["postalCode"]
            assert response.json["phoneNumber"] == user.phoneNumber
            assert user.phoneNumber == data["phoneNumber"]
            assert response.json["departementCode"] == user.departementCode
            assert user.departementCode == data["departementCode"]

        @pytest.mark.usefixtures("db_session")
        def when_updating_serialization(self, app):
            # given
            user = UserFactory(address="1 rue des machines")
            data = {
                "publicName": "Anne",
                "email": "new@example.com",
                "postalCode": "93020",
                "phoneNumber": "1234567890",
                "departementCode": "97",
                "hasSeenTutorials": True,
            }

            # when
            response = (
                TestClient(app.test_client()).with_auth(email=user.email).patch("/beneficiaries/current", json=data)
            )

            # then
            assert set(response.json.keys()) == {
                "activity",
                "address",
                "city",
                "civility",
                "dateCreated",
                "dateOfBirth",
                "departementCode",
                "deposit_version",
                "email",
                "expenses",
                "firstName",
                "hasAllowedRecommendations",
                "hasPhysicalVenues",
                "id",
                "isActive",
                "isAdmin",
                "isBeneficiary",
                "isEmailValidated",
                "lastName",
                "needsToFillCulturalSurvey",
                "needsToSeeTutorials",
                "phoneNumber",
                "postalCode",
                "publicName",
                "suspensionReason",
                "wallet_balance",
                "wallet_date_created",
                "wallet_is_activated",
            }

    class Returns400:
        @pytest.mark.usefixtures("db_session")
        def when_changes_are_forbidden(self, app):
            # given
            user = create_user(is_beneficiary=True, is_admin=False)
            repository.save(user)
            user_id = user.id

            data = {
                "isAdmin": True,
                "isBeneficiary": False,
                "firstName": "Jean",
                "lastName": "Martin",
                "dateCreated": "2018-08-01 12:00:00",
                "resetPasswordToken": "abc",
                "resetPasswordTokenValidityLimit": "2020-07-01 12:00:00",
            }

            # when
            response = (
                TestClient(app.test_client()).with_auth(email=user.email).patch("/beneficiaries/current", json=data)
            )

            # then
            user = User.query.get(user_id)
            assert response.status_code == 400
            for key in data:
                assert response.json[key] == ["Vous ne pouvez pas changer cette information"]
