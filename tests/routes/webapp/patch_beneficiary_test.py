import datetime
import uuid

import pytest

from pcapi.core.users.factories import UserFactory
from pcapi.core.users.models import User
from pcapi.utils.date import format_into_utc_date
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


@pytest.mark.usefixtures("db_session")
def test_patch_beneficiary(app):
    user = UserFactory()
    data = {
        "publicName": "Anne",
    }

    client = TestClient(app.test_client()).with_auth(email=user.email)
    response = client.patch("/beneficiaries/current", json=data)

    assert user.publicName == data["publicName"]
    assert response.status_code == 200
    assert response.json == {
        "pk": user.id,
        "activity": None,
        "address": user.address,
        "city": "Paris",
        "civility": None,
        "domainsCredit": {
            "all": {"initial": 500.0, "remaining": 500.0},
            "digital": {"initial": 200.0, "remaining": 200.0},
            "physical": {"initial": 200.0, "remaining": 200.0},
        },
        "dateCreated": format_into_utc_date(user.dateCreated),
        "dateOfBirth": "2000-01-01T00:00:00Z",
        "departementCode": user.departementCode,
        "deposit_version": 1,
        "email": user.email,
        "expenses": [
            {"current": 0.0, "domain": "all", "limit": 500.0},
            {"current": 0.0, "domain": "digital", "limit": 200.0},
            {"current": 0.0, "domain": "physical", "limit": 200.0},
        ],
        "firstName": "Jeanne",
        "hasPhysicalVenues": False,
        "id": humanize(user.id),
        "isActive": True,
        "isAdmin": False,
        "isBeneficiary": True,
        "isEmailValidated": True,
        "lastName": "Doux",
        "needsToFillCulturalSurvey": True,
        "needsToSeeTutorials": True,
        "phoneNumber": user.phoneNumber,
        "postalCode": user.postalCode,
        "publicName": "Anne",
        "suspensionReason": "",
        "wallet_balance": 500.0,
        "deposit_expiration_date": format_into_utc_date(user.deposit_expiration_date),
        "wallet_is_activated": True,
    }


@pytest.mark.usefixtures("db_session")
def test_patch_beneficiary_tutorial_related_attributes(app):
    user = UserFactory()

    client = TestClient(app.test_client()).with_auth(email=user.email)
    data = {"hasSeenTutorials": True}
    response = client.patch("/beneficiaries/current", json=data)

    assert response.status_code == 200


@pytest.mark.usefixtures("db_session")
def test_patch_beneficiary_survey_related_attributes(app):
    user = UserFactory()

    client = TestClient(app.test_client()).with_auth(email=user.email)
    survey_id = uuid.uuid4()
    data = {
        "needsToFillCulturalSurvey": False,
        "culturalSurveyId": str(survey_id),
        "culturalSurveyFilledDate": "2021-01-01T12:00:00Z",
    }
    response = client.patch("/beneficiaries/current", json=data)

    assert response.status_code == 200
    assert not user.needsToFillCulturalSurvey
    assert user.culturalSurveyId == survey_id
    assert user.culturalSurveyFilledDate == datetime.datetime(2021, 1, 1, 12, 0)


@pytest.mark.usefixtures("db_session")
def test_reject_pro_user(app):
    pro = UserFactory(isBeneficiary=False)
    initial = {
        "email": pro.email,
        "publicName": pro.publicName,
    }
    data = {
        "email": "new@example.com",
        "publicName": "New name",
    }
    client = TestClient(app.test_client()).with_auth(email=pro.email)
    response = client.patch("/beneficiaries/current", json=data)

    assert response.status_code == 400
    pro = User.query.get(pro.id)
    assert pro.email == initial["email"]
    assert pro.publicName == initial["publicName"]


@pytest.mark.usefixtures("db_session")
def test_forbid_some_attributes(app):
    user = UserFactory()
    # It's tedious to test all attributes. We focus on the most sensitive ones.
    forbidden_attributes = {
        "email": "new@example.com",
        "isAdmin": True,
        "isBeneficiary": False,
        "firstName": "Jean",
        "lastName": "Martin",
        "dateCreated": "2018-08-01 12:00:00",
        "resetPasswordToken": "abc",
        "resetPasswordTokenValidityLimit": "2020-07-01 12:00:00",
    }

    client = TestClient(app.test_client()).with_auth(email=user.email)

    for attribute, value in forbidden_attributes.items():
        response = client.patch("/beneficiaries/current", json={attribute: value})
        assert response.status_code == 400
        assert response.json[attribute] == ["Vous ne pouvez pas changer cette information"]
        user = User.query.get(user.id)
        assert getattr(user, attribute) != value
