import pytest

import pcapi.core.offers.factories as offers_factories
from pcapi.core.search.backends.appsearch import AppSearchBackend


pytestmark = pytest.mark.usefixtures("db_session")


def test_serialize():
    pass  # FIXME


def test_do_no_return_booleans():
    # If the backend's `serialize()` method returned boolean values,
    # they would be left as booleans when JSON-encoded, and the App
    # Search API would reject them (because it does not support this
    # data type).

    offer = offers_factories.OfferFactory()
    serialized = AppSearchBackend().serialize_offer(offer)
    for key, value in serialized.items():
        assert not isinstance(value, bool), f"Key {key}should not be a boolean"
