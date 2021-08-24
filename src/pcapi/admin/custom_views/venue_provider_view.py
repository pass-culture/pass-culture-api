from flask import flash
from flask import request
from flask import url_for
from markupsafe import Markup
from markupsafe import escape
from sqlalchemy.orm import query
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import Form
from wtforms.form import BaseForm
from wtforms.validators import Optional
from wtforms.validators import ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

from pcapi.admin.base_configuration import BaseAdminView
from pcapi.core.offerers.models import Venue
from pcapi.core.providers import api
from pcapi.core.providers.exceptions import NoAllocinePivot
from pcapi.core.providers.exceptions import NoPriceSpecified
from pcapi.core.providers.exceptions import NoSiretSpecified
from pcapi.core.providers.exceptions import ProviderNotFound
from pcapi.core.providers.exceptions import ProviderWithoutApiImplementation
from pcapi.core.providers.exceptions import VenueProviderException
from pcapi.core.providers.exceptions import VenueSiretNotRegistered
from pcapi.core.providers.models import VenueProvider
from pcapi.core.providers.models import VenueProviderCreationPayload
from pcapi.core.providers.repository import get_enabled_providers_for_pro_query
from pcapi.workers.venue_provider_job import venue_provider_job


def _venue_link(view, context, model, name) -> Markup:
    url = url_for("venue.index_view", id=model.venueId)
    return Markup('<a href="{}">Lieu associé</a>').format(escape(url))


def _get_venue_name_and_id(venue: Venue) -> str:
    return f"{venue.name} (#{venue.id})"


class VenueProviderView(BaseAdminView):
    can_edit = True
    can_create = True
    can_delete = True

    column_list = [
        "id",
        "venue.name",
        "provider.name",
        "venueIdAtOfferProvider",
        "isActive",
        "provider.isActive",
        "venue_link",
    ]
    column_labels = {
        "venue": "Lieu",
        "venue.name": "Nom du lieu",
        "provider.name": "Provider",
        "venueIdAtOfferProvider": "Identifiant pivot (SIRET par défaut)",
        "isActive": "Import activé",
        "provider.isActive": "Provider activé",
        "venue_link": "Lien",
    }

    column_default_sort = ("id", True)
    column_searchable_list = ["venue.name", "provider.name"]
    column_filters = ["id", "venue.name", "provider.name"]

    form_columns = ["venue", "provider", "venueIdAtOfferProvider", "isActive"]

    form_args = dict(
        provider=dict(
            get_label="name",
        ),
        venue=dict(get_label=_get_venue_name_and_id, label="Nom du lieu"),
    )

    def get_query(self) -> query:
        return self._extend_query(super().get_query())

    def get_count_query(self) -> query:
        return self._extend_query(super().get_count_query())

    @property
    def column_formatters(self):
        formatters = super().column_formatters
        formatters.update(venue_link=_venue_link)
        return formatters

    @staticmethod
    def _extend_query(query_to_override: query) -> query:
        venue_id = request.args.get("id")

        if venue_id:
            return query_to_override.filter(VenueProvider.venueId == venue_id)

        return query_to_override

    def scaffold_form(self) -> BaseForm:
        form_class = super().scaffold_form()
        form_class.provider = QuerySelectField(query_factory=get_enabled_providers_for_pro_query, get_label="name")
        form_class.price = DecimalField("Prix (Exclusivement et obligatoirement pour Allociné) ", [Optional()])
        form_class.isDuo = BooleanField("Offre duo (Exclusivement et obligatoirement pour Allociné)", [Optional()])

        return form_class

    def on_model_change(self, form: Form, model: VenueProvider, is_created: bool) -> None:
        venue_provider = None

        if (
            not is_created
            and not model.provider.isAllocine
            and form.provider.data.id == model.provider.id
            and form.venue.data.id == model.venue.id
        ):
            return super().on_model_change(form, model, is_created)

        try:
            venue_provider = api.create_venue_provider(
                form.provider.data.id,
                form.venue.data.id,
                VenueProviderCreationPayload(
                    isDuo=bool(form.isDuo.data),
                    price=form.price.data,
                    venueIdAtOfferProvider=form.venueIdAtOfferProvider.data,
                ),
            )
            venue_provider_job.delay(venue_provider.id)
        except VenueSiretNotRegistered as exc:
            flash(
                f"L'api de {exc.provider_name} ne répond pas pour le SIRET {exc.siret}",
                "error",
            )
            raise ValidationError("VenueSiretNotRegistered")
        except NoSiretSpecified:
            flash("Le siret du lieu n'est pas défini, veuillez en définir un", "error")
            raise ValidationError("NoSiretSpecified")
        except ProviderNotFound:
            flash("Aucun provider actif n'a été trouvé", "error")
            raise ValidationError("ProviderNotFound")
        except ProviderWithoutApiImplementation:
            flash("Le provider choisir n'implémente pas notre api", "error")
            raise ValidationError("ProviderWithoutApiImplementation")
        except NoAllocinePivot:
            flash("Aucun AllocinePivot n'est défini pour ce lieu", "error")
            raise ValidationError("NoAllocinePivot")
        except NoPriceSpecified:
            flash("Il est obligatoire de saisir un prix", "error")
            raise ValidationError("NoPriceSpecified")
        except VenueProviderException:
            flash("Le provider n'a pas pu être enregistré", "error")
            raise ValidationError("VenueProviderException")

        return venue_provider
