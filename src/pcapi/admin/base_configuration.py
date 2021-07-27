import logging
import secrets

import flask
import flask_admin
import flask_admin.base
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_admin.helpers import get_form_data
import flask_login
from werkzeug.utils import redirect

from pcapi.core.users import models as users_models
from pcapi.flask_app import oauth
from pcapi.models.db import db


logger = logging.getLogger(__name__)


class BaseAdminMixin:
    # We need to override `create_form()` and `edit_form()`, otherwise
    # Flask-Admin loads the form classes from its cache, which is
    # populated when the admin view is registered. It does not work
    # for us because we want the form to be different depending on the
    # logged-in user's privileges (see `form_columns()`). Thus, we
    # don't use the cache.
    def create_form(self, obj=None):
        form_class = self.get_create_form()
        return form_class(get_form_data(), obj=obj)

    def edit_form(self, obj=None):
        form_class = self.get_edit_form()
        return form_class(get_form_data(), obj=obj)

    def is_accessible(self) -> bool:
        authorized = flask_login.current_user.is_authenticated and flask_login.current_user.isAdmin
        if not authorized:
            logger.warning(
                "[ADMIN] Tentative d'accès non autorisé à l'interface d'administation par %s", flask_login.current_user
            )

        return authorized


class BaseAdminView(BaseAdminMixin, ModelView):
    page_size = 25
    can_set_page_size = True
    can_create = False
    can_edit = False
    can_delete = False
    form_base_class = SecureForm

    def inaccessible_callback(self, name, **kwargs):
        return redirect(flask.url_for("admin.index"))

    def after_model_change(self, form, model, is_created):
        action = "Création" if is_created else "Modification"
        model_name = str(model)
        logger.info("[ADMIN] %s du modèle %s par l'utilisateur %s", action, model_name, flask_login.current_user)

    def check_super_admins(self) -> bool:
        # `current_user` may be None, here, because this function
        # is (also) called when admin views are registered and
        # Flask-Admin populates its form cache.
        if not flask_login.current_user or not flask_login.current_user.is_authenticated:
            return False
        return flask_login.current_user.is_super_admin()


class BaseCustomAdminView(BaseAdminMixin, flask_admin.base.BaseView):
    def check_super_admins(self) -> bool:
        # `current_user` may be None, here, because this function
        # is (also) called when admin views are registered and
        # Flask-Admin populates its form cache.
        if not flask_login.current_user or not flask_login.current_user.is_authenticated:
            return False
        return flask_login.current_user.is_super_admin()


class AdminIndexView(flask_admin.base.AdminIndexView):
    @flask_admin.expose("/")
    def index(self):
        if not flask_login.current_user.is_authenticated:
            return redirect(flask.url_for(".login_view"))
        return super().index()

    @flask_admin.expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        redirect_uri = flask.url_for(".authorize", _external=True)
        return oauth.google.authorize_redirect(redirect_uri)

    @flask_admin.expose("/logout/")
    def logout_view(self):
        from pcapi.utils import login_manager

        flask_login.logout_user()
        login_manager.discard_session()
        return redirect(flask.url_for(".index"))

    @flask_admin.expose("/authorize/")
    def authorize(self):
        from pcapi.utils import login_manager

        token = oauth.google.authorize_access_token()
        google_user = oauth.google.parse_id_token(token)
        db_user = users_models.User.query.filter_by(email=google_user["email"]).one_or_none()
        if not db_user:
            db_user = users_models.User(
                firstName=google_user["given_name"],
                lastName=google_user["family_name"],
                email=google_user["email"],
                publicName=google_user["name"],
                isEmailValidated=True,
                isBeneficiary=False,
                isActive=True,
            )
            # generate a random password as the user won't login to anything else.
            db_user.setPassword(secrets.token_urlsafe(20))
            db_user.add_admin_role()
            db.session.add(db_user)
            db.session.commit()

        flask_login.login_user(db_user, remember=True)
        login_manager.stamp_session(db_user)
        return redirect(flask.url_for(".index"))
