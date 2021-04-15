from flask.helpers import flash
from flask_admin.helpers import get_form_data
from sqlalchemy.orm import query
from sqlalchemy.sql.functions import func
from wtforms import Form
from wtforms import SelectField
from wtforms.validators import DataRequired

from pcapi import settings
from pcapi.admin.base_configuration import BaseAdminView
from pcapi.admin.custom_views.mixins.suspension_mixin import SuspensionMixin
from pcapi.core.users.api import create_reset_password_token
from pcapi.core.users.models import User
from pcapi.domain.user_emails import send_activation_email
from pcapi.models import UserOfferer
from pcapi.utils.mailing import build_pc_webapp_reset_password_link
from pcapi.workers.push_notification_job import update_user_attributes_job


class BeneficiaryUserView(SuspensionMixin, BaseAdminView):
    can_edit = True

    @property
    def can_create(self) -> bool:
        return self.check_super_admins()

    column_list = [
        "id",
        "isBeneficiary",
        "email",
        "firstName",
        "lastName",
        "publicName",
        "dateOfBirth",
        "departementCode",
        "phoneNumber",
        "postalCode",
        "isEmailValidated",
        "deposit_version",
        "actions",
    ]
    column_labels = dict(
        email="Email",
        isBeneficiary="Est bénéficiaire",
        firstName="Prénom",
        lastName="Nom",
        publicName="Nom d'utilisateur",
        dateOfBirth="Date de naissance",
        departementCode="Département",
        phoneNumber="Numéro de téléphone",
        postalCode="Code postal",
        isEmailValidated="Email validé ?",
        deposit_version="Version du dépot",
    )
    column_searchable_list = ["id", "publicName", "email", "firstName", "lastName"]
    column_filters = ["postalCode", "isBeneficiary", "isEmailValidated"]

    @property
    def form_columns(self):
        fields = (
            "email",
            "dateOfBirth",
            "departementCode",
            "postalCode",
            "phoneNumber",
        )
        if self.check_super_admins():
            fields += ("firstName", "lastName")
        return fields

    form_args = dict(
        firstName=dict(validators=[DataRequired()]),
        lastName=dict(validators=[DataRequired()]),
        dateOfBirth=dict(validators=[DataRequired()]),
        postalCode=dict(validators=[DataRequired()]),
    )

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

    def get_create_form(self):
        form_class = super().scaffold_form()

        if not settings.IS_PROD:
            form_class.depositVersion = SelectField(
                "Version du déposit",
                [DataRequired()],
                choices=[
                    (1, "500€ - Deux seuils de dépense (300€ en physique et 200€ en numérique)"),
                    (2, "300€ - Un seuil de dépense (100€ en offres numériques)"),
                ],
            )

        return form_class

    def on_model_change(self, form: Form, model: User, is_created: bool) -> None:
        model.publicName = f"{model.firstName} {model.lastName}"

        if is_created:
            model.isBeneficiary = True
            # This is to prevent a circulary import dependency
            from pcapi.core.users.api import fulfill_beneficiary_data

            deposit_version = int(form.depositVersion.data) if not settings.IS_PROD else None
            fulfill_beneficiary_data(model, "pass-culture-admin", deposit_version)

        super().on_model_change(form, model, is_created)

    def after_model_change(self, form: Form, model: User, is_created: bool) -> None:
        update_user_attributes_job.delay(model.id)
        token = create_reset_password_token(model)
        if is_created and not send_activation_email(model, token=token):
            flash(
                f"L'envoi d'email a échoué. Le mot de passe peut être réinitialisé depuis le lien suivant : {build_pc_webapp_reset_password_link(token.value)}",
                "error",
            )
        super().after_model_change(form, model, is_created)

    def get_query(self) -> query:
        return (
            User.query.outerjoin(UserOfferer).filter(UserOfferer.userId.is_(None)).filter(User.isBeneficiary.is_(True))
        )

    def get_count_query(self) -> query:
        return (
            self.session.query(func.count("*"))
            .select_from(self.model)
            .outerjoin(UserOfferer)
            .filter(UserOfferer.userId.is_(None))
            .filter(User.isBeneficiary.is_(True))
        )
