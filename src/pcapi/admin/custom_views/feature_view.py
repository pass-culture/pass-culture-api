import logging

import flask_login

from pcapi.admin.base_configuration import BaseAdminView


logger = logging.getLogger(__name__)


class FeatureView(BaseAdminView):
    can_edit = True
    column_list = ["name", "description", "isActive"]
    column_labels = dict(name="Nom", description="Description", isActive="Activé")
    form_columns = ["isActive"]

    def on_model_change(self, form, model, is_created):
        logger.info(
            "Activated or deactivated feature flag",
            extra={"feature": model.name, "active": model.isActive, "changed_by": flask_login.current_user.email},
        )
        return super().on_model_change(form=form, model=model, is_created=is_created)
