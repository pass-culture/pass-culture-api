from unittest.mock import patch

import pytest

from pcapi.model_creators.generic_creators import create_mediation
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_recommendation
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_offer_with_event_product
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.model_creators.specific_creators import create_product_with_event_type
from pcapi.model_creators.specific_creators import create_product_with_thing_type


pytestmark = pytest.mark.usefixtures("db_session")


def test_model_thumb_url_should_use_mediation_first_as_thumb_url():
    # given
    user = create_user(email="user@example.com")
    offerer = create_offerer()
    venue = create_venue(offerer)
    product = create_product_with_event_type()
    offer = create_offer_with_event_product(product=product, venue=venue)
    mediation = create_mediation(offer, idx=1, thumb_count=1)

    # when
    recommendation = create_recommendation(offer, user, mediation=mediation)
    recommendation.mediationId = 1

    # then
    assert recommendation.thumbUrl == "http://localhost/storage/thumbs/mediations/AE"


def test_model_thumb_url_should_have_thumb_url_using_product_id_when_no_mediation():
    # given
    product = create_product_with_thing_type(thumb_count=1)
    product.id = 2
    offerer = create_offerer()
    venue = create_venue(offerer=offerer)
    offer = create_offer_with_thing_product(product=product, venue=venue)

    # when
    recommendation = create_recommendation(offer)

    # then
    assert recommendation.thumbUrl == "http://localhost/storage/thumbs/products/A9"


@patch("pcapi.settings.OBJECT_STORAGE_URL", "https://passculture.app/storage/v2")
def test_model_should_use_settings_variable():
    # given
    user = create_user(email="user@example.com")
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_event_product(venue)
    mediation = create_mediation(offer, idx=1, thumb_count=1)

    # when
    recommendation = create_recommendation(offer, user, mediation=mediation)
    recommendation.mediationId = 1

    # then
    assert recommendation.thumbUrl == "https://passculture.app/storage/v2/thumbs/mediations/AE"
