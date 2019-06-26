from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time

from models.pc_object import serialize
from models.user import User
from tests.conftest import clean_database, TestClient

BASE_DATA = {
    'email': 'toto@btmx.fr',
    'firstName': 'Toto',
    'lastName': 'Martin',
    'postalCode': '93100',
    'publicName': 'Toto',
    'password': '__v4l1d_P455sw0rd__',
    'contact_ok': 'true',
    'phoneNumber': '0612345678',
    'dateOfBirth': serialize(datetime(2001, 1, 1)),
}


class Post:
    class Returns201:
        @clean_database
        @freeze_time('2019-01-01 01:00:00')
        @patch('routes.signup.get_authorized_emails_and_dept_codes')
        def when_data_is_accurate(self, get_authorized_emails_and_dept_codes, app):
            # Given
            data = BASE_DATA.copy()
            expected_response_json = {'canBookFreeOffers': False,
                                      'departementCode': '93',
                                      'email': 'toto@btmx.fr',
                                      'firstName': 'Toto',
                                      'isAdmin': False,
                                      'lastName': 'Martin',
                                      'modelName': 'User',
                                      'phoneNumber': '0612345678',
                                      'postalCode': '93100',
                                      'publicName': 'Toto',
                                      'wallet_balance': 0,
                                      'dateOfBirth': '2001-01-01T00:00:00Z'}
            other_expected_keys = {'id', 'dateCreated'}
            get_authorized_emails_and_dept_codes.return_value = (['toto@btmx.fr'], ['93'])

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp', json=data)

            # Then
            assert response.status_code == 201
            assert 'Set-Cookie' not in response.headers
            json = response.json
            for key, value in expected_response_json.items():
                if key != 'dateCreated':
                    assert json[key] == value
            for key in other_expected_keys:
                assert key in json

        @clean_database
        def test_created_user_does_not_have_validation_token_and_cannot_book_free_offers(self, app):
            data = BASE_DATA.copy()

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 201
            assert 'validationToken' not in response.json
            created_user = User.query.filter_by(email='toto@btmx.fr').first()
            assert created_user.validationToken is None
            assert not created_user.canBookFreeOffers

        @clean_database
        def test_does_not_allow_the_creation_of_admins(self, app):
            # Given
            user_json = {
                'email': 'pctest.isAdmin.canBook@btmx.fr',
                'publicName': 'IsAdmin CanBook',
                'firstName': 'IsAdmin',
                'lastName': 'CanBook',
                'postalCode': '93100',
                'password': '__v4l1d_P455sw0rd__',
                'contact_ok': 'true',
                'isAdmin': True,
                'canBookFreeOffers': True
            }

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=user_json, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 201
            created_user = User.query.filter_by(email='pctest.isAdmin.canBook@btmx.fr').one()
            assert not created_user.isAdmin

        @clean_database
        def test_created_user_does_not_have_validation_token_and_cannot_book_free_offers(self, app):
            data = BASE_DATA.copy()

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 201
            assert 'validationToken' not in response.json
            created_user = User.query.filter_by(email='toto@btmx.fr').first()
            assert created_user.needsToFillCulturalSurvey == True

        @clean_database
        def when_calling_old_route(self, app):
            # Given
            data = BASE_DATA.copy()

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 308
            assert response.headers.get('Location') == 'http://localhost/users/signup/webapp'

    class Returns400:
        @clean_database
        def when_email_missing(self, app):
            # Given
            data = BASE_DATA.copy()
            del (data['email'])

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'email' in error

        @clean_database
        def when_email_with_invalid_format(self, app):
            # Given
            data = BASE_DATA.copy()
            data['email'] = 'toto'

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'email' in error

        @clean_database
        def when_email_is_already_used(self, app):
            TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=BASE_DATA, headers={'origin': 'http://localhost:3000'})

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=BASE_DATA, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'email' in error

        @clean_database
        def when_public_name_is_missing(self, app):
            # Given
            data = BASE_DATA.copy()
            del (data['publicName'])

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'publicName' in error

        @clean_database
        def when_public_name_is_too_short(self, app):
            # Given
            data = BASE_DATA.copy()
            data['publicName'] = 't'

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'publicName' in error

        @clean_database
        def when_public_name_is_too_long(self, app):
            # Given
            data = BASE_DATA.copy()
            data['publicName'] = 'x' * 102

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'publicName' in error

        @clean_database
        def when_password_is_missing(self, app):
            # Given
            data = BASE_DATA.copy()
            del (data['password'])

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'password' in error

        @clean_database
        def when_password_is_invalid(self, app):
            # Given
            data = BASE_DATA.copy()
            data['password'] = 'weakpassword'

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            response = response.json
            assert 'password' in response

        @clean_database
        def when_missing_contact_ok(self, app):
            data = BASE_DATA.copy()
            del (data['contact_ok'])

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'contact_ok' in error

        @clean_database
        def when_wrong_format_on_contact_ok(self, app):
            data = BASE_DATA.copy()
            data['contact_ok'] = 't'

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'contact_ok' in error

        @clean_database
        @patch('connectors.google_spreadsheet.get_authorized_emails_and_dept_codes')
        def when_user_not_in_exp_spreadsheet(self, get_authorized_emails_and_dept_codes, app):
            # Given
            get_authorized_emails_and_dept_codes.return_value = (['toto@email.com', 'other@email.com'], ['93', '93'])
            data = BASE_DATA.copy()
            data['email'] = 'unknown@unknown.com'

            # When
            response = TestClient(app.test_client()) \
                .post('/users/signup/webapp',
                      json=data, headers={'origin': 'http://localhost:3000'})

            # Then
            assert response.status_code == 400
            error = response.json
            assert 'email' in error
