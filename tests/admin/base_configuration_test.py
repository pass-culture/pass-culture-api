from unittest.mock import Mock
from unittest.mock import patch

import flask_login
import pytest

from pcapi.admin.base_configuration import BaseAdminView
from pcapi.core.testing import override_settings
from pcapi.core.users import factories as users_factories
from pcapi.core.users import models as users_models
from pcapi.flask_app import db
from pcapi.models import Booking


fake_db_session = [Mock()]


class DummyAdminView(BaseAdminView):
    pass


class AnonymousUser(flask_login.AnonymousUserMixin):
    pass


class DefaultConfigurationTest:
    def test_model_in_admin_view_is_not_deletable(self):
        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert view.can_delete is False, "Deletion from admin views is strictly forbidden to guarantee data consistency"

    def test_model_in_admin_view_is_not_creatable(self):
        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert view.can_create is False, "Creation from admin views is strictly forbidden to guarantee data consistency"

    def test_model_in_admin_view_is_not_editable_by_default(self):
        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert (
            view.can_edit is False
        ), "Edition from admin views is disabled by default. It can be enabled on a custom view"


class IsAccessibleTest:
    @patch("flask_login.utils._get_user")
    def test_access_is_forbidden_for_anonymous_users(self, get_user):
        # given
        get_user.return_value = AnonymousUser()

        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert not view.is_accessible()

    @patch("flask_login.utils._get_user")
    def test_access_is_forbidden_for_non_admin_users(self, get_user):
        # given
        get_user.return_value = users_factories.UserFactory.build(isAdmin=False)

        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert not view.is_accessible()

    @patch("flask_login.utils._get_user")
    def test_access_is_authorized_for_admin_users(self, get_user):
        # given
        get_user.return_value = users_factories.UserFactory.build(isAdmin=True)

        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert view.is_accessible() is True

    @patch("flask_login.utils._get_user")
    @override_settings(SUPER_ADMIN_EMAIL_ADDRESSES="", IS_PROD=True)
    def test_check_super_admins_is_false_for_non_super_admin_users(self, get_user):
        # given
        get_user.return_value = users_factories.UserFactory.build(email="dummy@email.com")

        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert view.check_super_admins() is False

    @patch("flask_login.utils._get_user")
    @override_settings(SUPER_ADMIN_EMAIL_ADDRESSES="super@admin.user", IS_PROD=True)
    def test_check_super_admins_is_true_for_super_admin_users(self, get_user):
        # given
        get_user.return_value = users_factories.UserFactory.build(email="super@admin.user")

        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert view.check_super_admins() is True

    @patch("flask_login.utils._get_user")
    @override_settings(SUPER_ADMIN_EMAIL_ADDRESSES="")
    def test_check_super_admins_is_deactived_in_non_prod_environments(self, get_user):
        # given
        get_user.return_value = users_factories.UserFactory.build(email="dummy@email.com", isAdmin=True)

        # when
        view = DummyAdminView(Booking, fake_db_session)

        # then
        assert view.check_super_admins() is True


class DummyUserView(BaseAdminView):
    @property
    def form_columns(self):
        fields = ("email",)
        if self.check_super_admins():
            fields += ("firstName", "lastName")
        return fields


class BaseAdminFormTest:
    def test_ensure_no_cache(self, app):
        view = DummyUserView(name="user", url="/user", model=users_models.User, session=db.session)
        with app.test_request_context(method="POST", data={}):
            with patch.object(view, "check_super_admins", return_value=True):
                form = view.get_edit_form()
                assert hasattr(form, "firstName")
                assert hasattr(form, "lastName")

            with patch.object(view, "check_super_admins", return_value=False):
                form = view.get_edit_form()
                assert hasattr(form, "firstName") is False
                assert hasattr(form, "lastName") is False


@pytest.mark.usefixtures("db_session")
class GoogleLoginTest:
    # @override_settings(GOOGLE_CLIENT_ID="client-id", GOOGLE_CLIENT_SECRET="client-secret")
    # def test_login_end_to_end(self, client):
    #     response = client.get("/pc/back-office/")
    #     assert response.status_code == 302
    #     assert response.headers["Location"] == "http://localhost/pc/back-office/login/"

    #     response = client.get("/pc/back-office/login")
    #     assert response.status_code == 302

    #     requests_mock.register_uri(
    #         "GET",
    #         "https://accounts.google.com/o/oauth2/v2/auth",
    #         headers={"Location": flask.url_for(".authorize")},
    #         status_code=302,
    #     )

    #     response = requests.get(response.headers["Location"])
    #     import ipdb

    #     ipdb.set_trace()

    @patch("pcapi.admin.base_configuration.oauth.google.authorize_access_token")
    @patch("pcapi.admin.base_configuration.oauth.google.parse_id_token")
    def test_authorize(self, parse_id_token, authorize_access_token, client):
        parse_id_token.return_value = {
            "email": "firstname.lastname@passculture.app",
            "family_name": "Lastname",
            "given_name": "Firstname",
            "name": "Firstname Lastname",
        }
        response = client.get("/pc/back-office/authorize")
        assert response.status_code == 302

        user = users_models.User.query.filter_by(email="firstname.lastname@passculture.app").one_or_none()

        assert user.firstName == "Firstname"
        assert user.lastName == "Lastname"
        assert user.isAdmin
        assert user.has_admin_role

        client.with_auth(user.email)
        response = client.get("/pc/back-office/")
        assert response.status_code == 200
        assert (
            "Bonjour <strong>Firstname Lastname</strong>, bienvenue dans le back office du pass Culture !"
            in response.data.decode()
        )

    @patch("pcapi.admin.base_configuration.oauth.google.authorize_access_token")
    @patch("pcapi.admin.base_configuration.oauth.google.parse_id_token")
    def test_authorize_user_already_exists(self, parse_id_token, authorize_access_token, client):
        parse_id_token.return_value = {
            "email": "firstname.lastname@passculture.app",
            "family_name": "Lastname",
            "given_name": "Firstname",
            "name": "Firstname Lastname",
        }
        users_factories.AdminFactory(email="firstname.lastname@passculture.app")
        response = client.get("/pc/back-office/authorize")
        assert response.status_code == 302

        user = users_models.User.query.filter_by(email="firstname.lastname@passculture.app").one_or_none()

        client.with_auth(user.email)
        response = client.get("/pc/back-office/")
        assert response.status_code == 200
        assert (
            f"Bonjour <strong>{user.firstName} {user.lastName}</strong>, bienvenue dans le back office du pass Culture !"
            in response.data.decode()
        )
