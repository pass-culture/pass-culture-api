from datetime import datetime
from unittest.mock import patch

import pytest

from pcapi.admin.custom_views.beneficiary_user_view import BeneficiaryUserView
from pcapi.admin.custom_views.mixins.suspension_mixin import _allow_suspension_and_unsuspension
import pcapi.core.mails.testing as mails_testing
import pcapi.core.users.factories as users_factories
from pcapi.core.users.models import User
from pcapi.models import Deposit

from tests.conftest import TestClient
from tests.conftest import clean_database


class BeneficiaryUserViewTest:
    @clean_database
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    def test_beneficiary_user_creation(self, mocked_validate_csrf_token, app):
        users_factories.UserFactory(email="admin@example.com", isAdmin=True)

        data = dict(
            email="lama@example.com",
            firstName="Serge",
            lastName="Lama",
            dateOfBirth="2002-07-13 10:05:00",
            departementCode="93",
            postalCode="93000",
            phoneNumber="0601020304",
            depositVersion="1",
            csrf_token="token",
        )

        client = TestClient(app.test_client()).with_auth("admin@example.com")
        response = client.post("/pc/back-office/beneficiary_users/new", form=data)

        assert response.status_code == 302

        user_created = User.query.filter_by(email="lama@example.com").one()
        assert user_created.firstName == "Serge"
        assert user_created.lastName == "Lama"
        assert user_created.publicName == "Serge Lama"
        assert user_created.dateOfBirth == datetime(2002, 7, 13, 10, 5)
        assert user_created.departementCode == "93"
        assert user_created.postalCode == "93000"
        assert user_created.phoneNumber == "0601020304"
        assert len(user_created.deposits) == 1
        assert user_created.deposit.source == "pass-culture-admin"
        assert user_created.deposit.amount == 500

        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data == {
            "FromEmail": "support@example.com",
            "Mj-TemplateID": 994771,
            "Mj-TemplateLanguage": True,
            "To": "lama@example.com",
            "Vars": {
                "prenom_user": "Serge",
                "token": user_created.resetPasswordToken,
                "email": "lama%40example.com",
                "env": "-development",
            },
        }

    @clean_database
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    def test_beneficiary_user_creation_for_deposit_v2(self, mocked_validate_csrf_token, app):
        users_factories.UserFactory(email="user@example.com", isAdmin=True)

        data = dict(
            email="toto@email.fr",
            firstName="Serge",
            lastName="Lama",
            dateOfBirth="2002-07-13 10:05:00",
            departementCode="93",
            postalCode="93000",
            phoneNumber="0601020304",
            depositVersion="2",
        )

        client = TestClient(app.test_client()).with_auth("user@example.com")
        response = client.post("/pc/back-office/beneficiary_users/new", form=data)

        assert response.status_code == 302

        user_created = User.query.filter_by(email="toto@email.fr").one()
        assert len(user_created.deposits) == 1
        assert user_created.deposit.version == 2
        assert user_created.deposit.source == "pass-culture-admin"
        assert user_created.deposit.amount == 300

    def test_the_deposit_version_is_specified(self, app, db_session):
        # Given
        beneficiary_view = BeneficiaryUserView(User, db_session)
        beneficiary_view_create_form = beneficiary_view.get_create_form()
        data = dict(
            email="toto@email.fr",
            firstName="Serge",
            lastName="Lama",
            dateOfBirth="2002-07-13 10:05:00",
            departementCode="93",
            postalCode="93000",
            phoneNumber="0601020304",
            depositVersion="2",
        )

        form = beneficiary_view_create_form(data=data)
        user = User()

        # When
        beneficiary_view.on_model_change(form, user, True)

        # Then
        assert user.deposit_version == 2

    @patch("pcapi.settings.IS_PROD", return_value=True)
    def test_form_has_no_deposit_field_for_production(self, app, db_session):
        # Given
        beneficiary_view = BeneficiaryUserView(User, db_session)
        beneficiary_view_create_form = beneficiary_view.get_create_form()
        form = beneficiary_view_create_form(data=(dict()))

        # then
        assert not hasattr(form, "depositVersion")

    @patch("pcapi.settings.IS_PROD", return_value=True)
    @patch("pcapi.settings.SUPER_ADMIN_EMAIL_ADDRESSES", return_value="")
    def test_beneficiary_user_creation_is_restricted_in_prod(
        self, is_prod_mock, super_admin_email_addresses, app, db_session
    ):
        users_factories.UserFactory(email="user@example.com", isAdmin=True)

        data = dict(
            email="toto@email.fr",
            firstName="Serge",
            lastName="Lama",
            dateOfBirth="2002-07-13 10:05:00",
            departementCode="93",
            postalCode="93000",
        )

        client = TestClient(app.test_client()).with_auth("user@example.com")
        response = client.post("/pc/back-office/beneficiary_users/new", form=data)

        assert response.status_code == 302

        filtered_users = User.query.filter_by(email="toto@email.fr").all()
        deposits = Deposit.query.all()
        assert len(filtered_users) == 0
        assert len(deposits) == 0

    @clean_database
    # FIXME (dbaty, 2020-12-16): I could not find a quick way to
    #  generate a valid CSRF token in tests. This should be fixed.
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    def test_suspend_beneficiary(self, mocked_validate_csrf_token, app):
        admin = users_factories.UserFactory(email="admin15@example.com", isAdmin=True)
        beneficiary = users_factories.UserFactory(email="user15@example.com")

        client = TestClient(app.test_client()).with_auth(admin.email)
        url = f"/pc/back-office/beneficiary_users/suspend?user_id={beneficiary.id}"
        data = {
            "reason": "fraud",
            "csrf_token": "token",
        }
        response = client.post(url, form=data)

        assert response.status_code == 302
        assert not beneficiary.isActive

    @clean_database
    # FIXME (dbaty, 2020-12-16): I could not find a quick way to
    #  generate a valid CSRF token in tests. This should be fixed.
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    def test_unsuspend_beneficiary(self, mocked_validate_csrf_token, app):
        admin = users_factories.UserFactory(email="admin15@example.com", isAdmin=True)
        beneficiary = users_factories.UserFactory(email="user15@example.com", isActive=False)

        client = TestClient(app.test_client()).with_auth(admin.email)
        url = f"/pc/back-office/beneficiary_users/unsuspend?user_id={beneficiary.id}"
        data = {
            "reason": "fraud",
            "csrf_token": "token",
        }
        response = client.post(url, form=data)

        assert response.status_code == 302
        assert beneficiary.isActive

    @clean_database
    @patch("pcapi.settings.IS_PROD", True)
    def test_suspend_beneficiary_is_restricted(self, app):
        admin = users_factories.UserFactory(email="admin@example.com", isAdmin=True)
        beneficiary = users_factories.UserFactory(email="user@example.com")

        client = TestClient(app.test_client()).with_auth(admin.email)
        url = f"/pc/back-office/beneficiary_users/suspend?user_id={beneficiary.id}"
        data = {
            "reason": "fraud",
            "csrf_token": "token",
        }
        response = client.post(url, form=data)

        assert response.status_code == 403

    @patch("pcapi.settings.IS_PROD", True)
    @patch("pcapi.settings.SUPER_ADMIN_EMAIL_ADDRESSES", ["super-admin@example.com", "boss@example.com"])
    @pytest.mark.usefixtures("db_session")
    def test_allow_suspension_and_unsuspension(self):
        basic_admin = users_factories.UserFactory(email="admin@example.com", isAdmin=True)
        assert not _allow_suspension_and_unsuspension(basic_admin)
        super_admin = users_factories.UserFactory(email="super-admin@example.com", isAdmin=True)
        assert _allow_suspension_and_unsuspension(super_admin)

    @clean_database
    @patch("pcapi.admin.custom_views.beneficiary_user_view.flash")
    @patch("wtforms.csrf.session.SessionCSRF.validate_csrf_token")
    def test_beneficiary_user_edition_does_not_send_email(self, mocked_validate_csrf_token, mocked_flask_flash, app):
        users_factories.UserFactory(email="user@example.com", isAdmin=True)
        user_to_edit = users_factories.UserFactory(email="not_yet_edited@email.com", isAdmin=False)

        data = dict(
            email="edited@email.com",
            firstName=user_to_edit.firstName,
            lastName=user_to_edit.lastName,
            dateOfBirth=user_to_edit.dateOfBirth,
            departementCode=user_to_edit.departementCode,
            postalCode=user_to_edit.postalCode,
        )

        client = TestClient(app.test_client()).with_auth("user@example.com")
        response = client.post(f"/pc/back-office/beneficiary_users/edit/?id={user_to_edit.id}", form=data)

        assert response.status_code == 302

        user_edited = User.query.filter_by(email="edited@email.com").one_or_none()
        assert user_edited is not None

        mocked_flask_flash.assert_not_called()
        assert not mails_testing.outbox
