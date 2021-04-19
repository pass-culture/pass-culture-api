from typing import Union

from flask import request
from flask import url_for
from markupsafe import Markup
from sqlalchemy.orm import query
from wtforms import Form

from pcapi.admin.base_configuration import BaseAdminView
from pcapi.core.offerers.models import Venue
from pcapi.core.offers.api import update_offer_and_stock_id_at_providers


def _offers_link(view, context, model, name) -> Markup:
    url = url_for("offer_for_venue.index", id=model.id)
    text = "Offres associées"

    return Markup(f'<a href="{url}">{text}</a>')


def _get_venue_provider_link(view, context, model, name) -> Union[Markup, None]:

    if not model.venueProviders:
        return None

    url = url_for("venue_providers.index_view", id=model.id)
    return Markup(f'<a href="{url}">Voir</a>')


class VenueView(BaseAdminView):
    can_edit = True
    column_list = [
        "id",
        "name",
        "siret",
        "city",
        "postalCode",
        "address",
        "offres",
        "publicName",
        "latitude",
        "longitude",
        "isPermanent",
        "offer_import",
    ]
    column_labels = dict(
        name="Nom",
        siret="SIRET",
        city="Ville",
        postalCode="Code postal",
        address="Adresse",
        publicName="Nom d'usage",
        latitude="Latitude",
        longitude="Longitude",
        isPermanent="Lieu permanent",
        offer_import="Import d'offres",
    )
    column_searchable_list = ["name", "siret", "publicName"]
    column_filters = ["postalCode", "city", "publicName"]
    form_columns = [
        "name",
        "siret",
        "city",
        "postalCode",
        "address",
        "publicName",
        "latitude",
        "longitude",
        "isPermanent",
    ]

    def get_query(self) -> query:
        return self._extend_query(super().get_query())

    def get_count_query(self) -> query:
        return self._extend_query(super().get_count_query())

    @staticmethod
    def _extend_query(query_to_override: query) -> query:
        venue_id = request.args.get("id")

        if venue_id:
            return query_to_override.filter(Venue.id == venue_id)

        return query_to_override

    @property
    def column_formatters(self):
        formatters = super().column_formatters
        formatters.update(offres=_offers_link)
        formatters.update(offer_import=_get_venue_provider_link)
        return formatters

    def update_model(self, new_venue_form: Form, venue: Venue) -> bool:
        has_siret_changed = new_venue_form.siret.data != venue.siret
        old_siret = venue.siret

        super().update_model(new_venue_form, venue)

        if has_siret_changed and old_siret:
            update_offer_and_stock_id_at_providers(venue, old_siret)

        return True
