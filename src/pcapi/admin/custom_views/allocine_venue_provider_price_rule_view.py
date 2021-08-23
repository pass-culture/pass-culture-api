from pcapi.admin.base_configuration import BaseAdminView


class AllocineVenueProviderPriceRuleView(BaseAdminView):
    can_edit = True
    column_list = [
        "allocineVenueProvider.venue.name",
        "allocineVenueProvider.venue.siret",
        "price",
    ]
    column_searchable_list = ["allocineVenueProvider.venue.siret"]
    column_sortable_list: list[str] = []
    column_labels = {
        "allocineVenueProvider.venue.name": "Nom du lieu",
        "allocineVenueProvider.venue.siret": "SIRET",
        "price": "Prix",
    }
    form_columns = ["price"]
