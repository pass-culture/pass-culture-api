from functools import wraps
from pathlib import Path
from pprint import pprint
from unittest.mock import Mock

from alembic import command
from alembic.config import Config
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
import pytest
from requests import Response
from requests.auth import _basic_auth_str

import pcapi
from pcapi import settings
from pcapi.admin.install import install_admin_views
import pcapi.core.mails.testing as mails_testing
import pcapi.core.object_storage.testing as object_storage_testing
import pcapi.core.testing
from pcapi.flask_app import admin
from pcapi.install_database_extensions import install_database_extensions
from pcapi.local_providers.install import install_local_providers
from pcapi.model_creators.generic_creators import PLAIN_DEFAULT_TESTING_PASSWORD
from pcapi.models.db import db
from pcapi.models.install import install_activity
from pcapi.notifications.push import testing as push_notifications_testing
from pcapi.repository.clean_database import clean_all_database
from pcapi.routes import install_routes
from pcapi.routes.native.v1.blueprint import native_v1
from pcapi.routes.pro.blueprints import pro_api_v2
from pcapi.utils.json_encoder import EnumJSONEncoder


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


def pytest_configure(config):
    if config.getoption("capture") == "no":
        TestClient.WITH_DOC = True


@pytest.fixture(scope="session")
def app():
    app = Flask(  # pylint: disable=redefined-outer-name
        __name__,
        template_folder=Path(pcapi.__path__[0]) / "templates",
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "@##&6cweafhv3426445"
    app.config["REMEMBER_COOKIE_HTTPONLY"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = False
    app.config["TESTING"] = True
    app.url_map.strict_slashes = False
    app.json_encoder = EnumJSONEncoder

    login_manager = LoginManager()
    login_manager.init_app(app)
    db.init_app(app)

    app.app_context().push()
    install_database_extensions(app)

    run_migrations()

    install_activity()
    install_routes(app)
    install_local_providers()
    admin.init_app(app)
    install_admin_views(admin, db.session)

    app.redis_client = Mock()
    app.register_blueprint(native_v1, url_prefix="/native/v1")
    app.register_blueprint(pro_api_v2, url_prefix="/v2")

    JWTManager(app)

    return app


@pytest.fixture(autouse=True)
def clear_mail_outbox():
    try:
        yield
    finally:
        mails_testing.reset_outbox()


@pytest.fixture(autouse=True)
def clear_push_notification_requests():
    try:
        yield
    finally:
        push_notifications_testing.reset_requests()


@pytest.fixture()
def clear_tests_assets_bucket():
    try:
        yield
    finally:
        object_storage_testing.reset_bucket()


def clean_database(f: object) -> object:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return_value = f(*args, **kwargs)
        finally:
            clean_all_database()
        return return_value

    return decorated_function


@pytest.fixture(scope="session")
def _db(app):  # pylint: disable=redefined-outer-name
    """
    Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
    database connection.
    """
    mock_db = db
    mock_db.init_app(app)
    install_database_extensions(app)
    run_migrations()

    install_activity()
    install_routes(app)
    install_local_providers()
    clean_all_database()

    return mock_db


pcapi.core.testing.register_event_for_assert_num_queries()


@pytest.fixture()
def assert_num_queries():
    return pcapi.core.testing.assert_num_queries


class TestClient:
    WITH_DOC = False
    USER_TEST_ADMIN_EMAIL = "pctest.admin93.0@example.com"
    LOCAL_ORIGIN_HEADERS = {"origin": "http://localhost:3000"}

    def __init__(self, client: FlaskClient):
        self.client = client
        self.auth_header = {}

    def with_auth(self, email: str = None):
        self.email = email
        if email is None:
            self.auth_header = {
                "Authorization": _basic_auth_str(TestClient.USER_TEST_ADMIN_EMAIL, PLAIN_DEFAULT_TESTING_PASSWORD),
            }
        else:
            self.auth_header = {
                "Authorization": _basic_auth_str(email, PLAIN_DEFAULT_TESTING_PASSWORD),
            }

        return self

    def delete(self, route: str, headers: dict = None):
        headers = headers or self.LOCAL_ORIGIN_HEADERS
        result = self.client.delete(route, headers={**self.auth_header, **headers})
        self._print_spec("DELETE", route, None, result)
        return result

    def get(self, route: str, headers=None):
        headers = headers or self.LOCAL_ORIGIN_HEADERS
        result = self.client.get(route, headers={**self.auth_header, **headers})
        self._print_spec("GET", route, None, result)
        return result

    def post(self, route: str, json: dict = None, form: dict = None, files: dict = None, headers: dict = None):
        headers = headers or self.LOCAL_ORIGIN_HEADERS
        if form or files:
            result = self.client.post(route, data=form if form else files, headers={**self.auth_header, **headers})
        else:
            result = self.client.post(route, json=json, headers={**self.auth_header, **headers})

        self._print_spec("POST", route, json, result)
        return result

    def patch(self, route: str, json: dict = None, headers: dict = None):
        headers = headers or self.LOCAL_ORIGIN_HEADERS
        result = self.client.patch(route, json=json, headers={**self.auth_header, **headers})
        self._print_spec("PATCH", route, json, result)
        return result

    def put(self, route: str, json: dict = None, headers: dict = None):
        headers = headers or self.LOCAL_ORIGIN_HEADERS
        result = self.client.put(route, json=json, headers={**self.auth_header, **headers})
        self._print_spec("PUT", route, json, result)
        return result

    def _print_spec(self, verb: str, route: str, request_body: dict, result: Response):
        if not TestClient.WITH_DOC:
            return

        print("\n===========================================")
        print("%s :: %s" % (verb, route))
        print("STATUS CODE :: %s" % result.status_code)

        if request_body:
            print("REQUEST BODY")
            pprint(request_body)

        if result.data:
            print("RESPONSE BODY")
            pprint(result.json)

        print("===========================================\n")
