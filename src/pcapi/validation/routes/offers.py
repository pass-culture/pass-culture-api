from pcapi.domain.allocine import get_editable_fields_for_allocine_offers
from pcapi.models import OfferSQLEntity, UserOfferer
from pcapi.models.api_errors import ResourceNotFoundError, ApiErrors
from pcapi.models.offer_type import ProductType


def check_user_has_rights_on_offerer(user_offerer: UserOfferer):
    errors = ApiErrors()
    errors.add_error(
        'global',
        "Vous n'avez pas les droits d'accès suffisant pour accéder à cette information."
    )
    errors.status_code = 403

    if user_offerer is None:
        raise errors

    if user_offerer.validationToken:
        raise errors


def check_venue_exists_when_requested(venue, venue_id):
    if venue_id and venue is None:
        errors = ResourceNotFoundError()
        errors.add_error(
            'global',
            "Ce lieu n'a pas été trouvé"
        )
        raise errors


def check_offer_type_is_valid(offer_type_name):
    if not ProductType.is_thing(offer_type_name) and not ProductType.is_event(offer_type_name):
        api_error = ApiErrors()
        api_error.add_error('type',
                            'Le type de cette offre est inconnu')
        raise api_error


def check_offer_name_length_is_valid(offer_name: str):
    max_offer_name_length = 90
    if len(offer_name) > max_offer_name_length:
        api_error = ApiErrors()
        api_error.add_error('name', 'Le titre de l’offre doit faire au maximum 90 caractères.')
        raise api_error


def check_offer_id_is_present_in_request(offer_id: str):
    if offer_id is None:
        errors = ApiErrors()
        errors.status_code = 400
        errors.add_error('global', 'Le paramètre offerId est obligatoire')
        errors.maybe_raise()
        raise errors


def check_offer_is_editable(offer: OfferSQLEntity):
    if not offer.isEditable:
        error = ApiErrors()
        error.status_code = 400
        error.add_error('global', "Les offres importées ne sont pas modifiables")
        raise error


def check_edition_for_allocine_offer_is_valid(payload: dict):
    editable_fields_for_offer = get_editable_fields_for_allocine_offers()

    all_payload_fields_are_editable = set(payload).issubset(editable_fields_for_offer)

    if not all_payload_fields_are_editable:
        list_of_non_editable_fields = set(payload).difference(editable_fields_for_offer)

        api_error = ApiErrors()
        for non_editable_field in list_of_non_editable_fields:
            api_error.add_error(non_editable_field, 'Vous ne pouvez pas modifier ce champ')

        raise api_error
