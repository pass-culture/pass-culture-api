from flask.helpers import flash
from sqlalchemy.orm import query
from sqlalchemy.sql.functions import func
from wtforms import Form
from wtforms import SelectField
from wtforms.validators import DataRequired

from pcapi import settings
from pcapi.admin.base_configuration import BaseAdminView
from pcapi.admin.custom_views.mixins.suspension_mixin import SuspensionMixin
from pcapi.core.users.models import User
from pcapi.domain.user_emails import send_activation_email
from pcapi.models import UserOfferer
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
        "validationToken",
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
        validationToken="Jeton de validation d'adresse email",
        deposit_version="Version du dépot",
    )
    column_searchable_list = ["id", "publicName", "email", "firstName", "lastName"]
    column_filters = ["postalCode", "isBeneficiary"]

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
    )

    def get_create_form(self):
        # XXX: do not depend on the logged-in user (or anything that
        # is runtime dependent) here because this function is called
        # when the class is initialized: creation and edition forms
        # are cached by Flask-Admin.
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
        update_user_attributes_job.delay(model)
        if is_created and not send_activation_email(model):
            flash("L'envoi d'email a échoué", "error")
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
