from pcapi.model_creators.specific_creators import create_product_with_thing_type
from pcapi.models import ApiErrors
from pcapi.models import ThingType
from pcapi.validation.models.product import validate


def test_should_return_error_message_when_product_is_digital_and_offline():
    # Given
    product = create_product_with_thing_type(is_offline_only=True, is_digital=True)
    api_errors = ApiErrors()

    # When
    api_error = validate(product, api_errors)

    # Then
    assert api_error.errors["url"] == ["Une offre de type Cinéma - cartes d'abonnement ne peut pas être numérique"]


def test_should_not_return_error_message_when_product_is_not_digital():
    # Given
    product = create_product_with_thing_type(is_offline_only=True, is_digital=False)
    api_errors = ApiErrors()

    # When
    api_error = validate(product, api_errors)

    # Then
    assert api_error.errors == {}


def test_should_not_return_error_message_when_product_is_online():
    # Given
    product = create_product_with_thing_type(is_offline_only=False, is_digital=False)
    api_errors = ApiErrors()

    # When
    api_error = validate(product, api_errors)

    # Then
    assert api_error.errors == {}
