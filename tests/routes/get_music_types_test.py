from sqlalchemy_api_handler import ApiHandler

from domain.music_types import music_types
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_user


class Get:
    class Returns200:
        @clean_database
        def when_list_music_types(self, app):
            # given
            user = create_user()
            ApiHandler.save(user)

            # when
            response = TestClient(app.test_client()).with_auth(user.email) \
                .get('/musicTypes')

            # then
            response_json = response.json
            assert response.status_code == 200
            assert response_json == music_types
