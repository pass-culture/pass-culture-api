import pytest
from sqlalchemy_api_handler import ApiErrors, ApiHandler

from tests.conftest import clean_database
from tests.test_utils import create_offerer, create_user, create_user_offerer


@clean_database
def test_save_user_offerer_raise_api_error_when_not_unique(app):
    # Given
    user = create_user()
    offerer = create_offerer()
    uo1 = create_user_offerer(user, offerer)
    ApiHandler.save(user, offerer, uo1)
    uo2 = create_user_offerer(user, offerer)

    # When
    with pytest.raises(ApiErrors) as error:
        ApiHandler.save(uo2)

    assert error.value.errors["global"] == ['Une entrée avec cet identifiant existe déjà dans notre base de données']
