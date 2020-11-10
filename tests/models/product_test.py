from unittest.mock import patch

import pytest

from pcapi.model_creators.specific_creators import create_product_with_thing_type
from pcapi.repository import repository
from pcapi.utils.human_ids import humanize


@pytest.mark.usefixtures("db_session")
@patch('pcapi.models.has_thumb_mixin.get_storage_base_url', return_value='http://storage/base/url')
def when_product_has_one_thumb(mock_get_storage_base, app):
    # Given
    product = create_product_with_thing_type(thumb_count=1)
    repository.save(product)
    product_id = humanize(product.id)

    # When
    thumb_url = product.thumbUrl

    # Then
    assert thumb_url == f'http://storage/base/url/thumbs/products/{product_id}'


@pytest.mark.usefixtures("db_session")
def when_product_has_no_thumb(app):
    # Given
    product = create_product_with_thing_type(thumb_count=0)
    repository.save(product)

    # When
    thumb_url = product.thumbUrl

    # Then
    assert thumb_url is None

