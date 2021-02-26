import datetime

import pytest

from pcapi.model_creators.generic_creators import create_user
from pcapi.models import UserSession
from pcapi.repository import repository
from pcapi.utils.date import format_into_utc_date
from pcapi.utils.human_ids import humanize

from tests.conftest import TestClient


class Post:
    class Returns200:
        @pytest.mark.usefixtures("db_session")
        def when_account_is_known(self, app):
            # given
            user = create_user(
                civility="M.",
                departement_code="93",
                email="user@example.com",
                first_name="Jean",
                last_name="Smisse",
                date_of_birth=datetime.datetime(2000, 1, 1),
                phone_number="0612345678",
                postal_code="93020",
                public_name="Toto",
                last_connection_date=datetime.datetime(2019, 1, 1),
            )
            user.isEmailValidated = True
            repository.save(user)
            data = {"identifier": user.email, "password": user.clearTextPassword}

            # when
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # then
            assert response.status_code == 200
            assert not any("password" in field.lower() for field in response.json)
            assert response.json == {
                "activity": None,
                "address": None,
                "city": None,
                "civility": "M.",
                "dateCreated": format_into_utc_date(user.dateCreated),
                "dateOfBirth": format_into_utc_date(user.dateOfBirth),
                "departementCode": "93",
                "email": "user@example.com",
                "firstName": "Jean",
                "hasAllowedRecommendations": False,
                "hasOffers": False,
                "hasPhysicalVenues": False,
                "hasSeenProTutorials": False,
                "id": humanize(user.id),
                "isAdmin": False,
                "isBeneficiary": True,
                "isEmailValidated": True,
                "lastConnectionDate": format_into_utc_date(user.lastConnectionDate),
                "lastName": "Smisse",
                "needsToFillCulturalSurvey": False,
                "phoneNumber": "0612345678",
                "postalCode": "93020",
                "publicName": "Toto",
            }

        @pytest.mark.usefixtures("db_session")
        def when_account_is_known_with_mixed_case_email(self, app):
            # given
            user = create_user(email="USER@example.COM")
            repository.save(user)
            data = {"identifier": "uSeR@EXAmplE.cOm", "password": user.clearTextPassword}

            # when
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # then
            assert response.status_code == 200

        @pytest.mark.usefixtures("db_session")
        def when_account_is_known_with_trailing_spaces_in_email(self, app):
            # given
            user = create_user(email="user@example.com")
            repository.save(user)
            data = {"identifier": "  user@example.com  ", "password": user.clearTextPassword}

            # when
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # then
            assert response.status_code == 200

        @pytest.mark.usefixtures("db_session")
        def expect_a_new_user_session_to_be_recorded(self, app):
            # given
            user = create_user(email="user@example.com")
            repository.save(user)
            data = {"identifier": user.email, "password": user.clearTextPassword}

            # when
            response = TestClient(app.test_client()).post(
                "/users/signin", json=data, headers={"origin": "http://localhost:3000"}
            )

            # then
            assert response.status_code == 200

            session = UserSession.query.filter_by(userId=user.id).first()
            assert session is not None

    class Returns401:
        @pytest.mark.usefixtures("db_session")
        def when_identifier_is_missing(self, app):
            # Given
            user = create_user()
            repository.save(user)
            data = {"identifier": None, "password": user.clearTextPassword}

            # When
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # Then
            assert response.status_code == 400
            assert response.json["identifier"] == ["none is not an allowed value"]

        @pytest.mark.usefixtures("db_session")
        def when_identifier_is_incorrect(self, app):
            # Given
            user = create_user()
            repository.save(user)
            data = {"identifier": "random.email@test.com", "password": user.clearTextPassword}

            # When
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # Then
            assert response.status_code == 401
            assert response.json["identifier"] == ["Identifiant ou mot de passe incorrect"]

        @pytest.mark.usefixtures("db_session")
        def when_password_is_missing(self, app):
            # Given
            user = create_user()
            repository.save(user)
            data = {"identifier": user.email, "password": None}

            # When
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # Then
            assert response.status_code == 400
            assert response.json["password"] == ["none is not an allowed value"]

        @pytest.mark.usefixtures("db_session")
        def when_password_is_incorrect(self, app):
            # Given
            user = create_user()
            repository.save(user)
            data = {"identifier": user.email, "password": "wr0ng_p455w0rd"}

            # When
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # Then
            assert response.status_code == 401
            assert response.json["identifier"] == ["Identifiant ou mot de passe incorrect"]

        @pytest.mark.usefixtures("db_session")
        def when_account_is_not_validated(self, app):
            # Given
            user = create_user()
            user.generate_validation_token()
            repository.save(user)
            data = {"identifier": user.email, "password": user.clearTextPassword}

            # When
            response = TestClient(app.test_client()).post("/users/signin", json=data)

            # Then
            assert response.status_code == 401
            assert response.json["identifier"] == ["Ce compte n'est pas validé."]
