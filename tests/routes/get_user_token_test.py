from sqlalchemy_api_handler import ApiHandler

from tests.conftest import clean_database, TestClient
from tests.test_utils import create_user


class Get:
    class Returns200:
        @clean_database
        def when_activation_token_exists(self, app):
            # given
            token = 'U2NCXTNB2'
            user = create_user(reset_password_token=token)
            ApiHandler.save(user)

            # when
            request = TestClient(app.test_client()).get('/users/token/' + token)

            # then
            assert request.status_code == 200

    class Returns404:
        @clean_database
        def when_activation_token_does_not_exist(self, app):
            # when
            request = TestClient(app.test_client()).get('/users/token/3YU26FS')

            # then
            assert request.status_code == 404
