from pcapi.core.categories.subcategories import ALL_SUBCATEGORIES_DICT
from pcapi.models.api_errors import ApiErrors
from pcapi.models.offer_type import ProductType


def check_offer_type_is_valid(offer_type_name):
    if not ProductType.is_thing(offer_type_name) and not ProductType.is_event(offer_type_name):
        api_error = ApiErrors()
        api_error.add_error("type", "Le type de cette offre est inconnu")
        api_error.add_error("subcategory", "La sous-catégorie de cette offre est inconnue")
        raise api_error


def check_offer_subcategory_is_valid(offer_subcategory_id):
    if offer_subcategory_id not in ALL_SUBCATEGORIES_DICT:
        api_error = ApiErrors()
        api_error.add_error("subcategory", "La sous-catégorie de cette offre est inconnue")
        raise api_error


def check_offer_name_length_is_valid(offer_name: str):
    max_offer_name_length = 90
    if len(offer_name) > max_offer_name_length:
        api_error = ApiErrors()
        api_error.add_error("name", "Le titre de l’offre doit faire au maximum 90 caractères.")
        raise api_error


def check_offer_id_is_present_in_request(offer_id: str):
    if offer_id is None:
        errors = ApiErrors()
        errors.status_code = 400
        errors.add_error("global", "Le paramètre offerId est obligatoire")
        errors.maybe_raise()
        raise errors


def check_offer_isbn_is_valid(isbn: str):
    isbn_length = 13
    if not (isbn and isbn.isnumeric() and len(isbn) == isbn_length):
        api_errors = ApiErrors()
        api_errors.add_error("isbn", "Format d’ISBN incorrect. Exemple de format correct : 9782020427852")
        raise api_errors


def check_offer_not_duo_and_educational(is_duo: bool, is_educational: bool):
    if is_duo and is_educational:
        api_errors = ApiErrors()
        api_errors.add_error("educational", "An offer cannot be both 'duo' and 'educational'")
        raise api_errors
