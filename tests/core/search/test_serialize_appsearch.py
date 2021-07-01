import pytest

import pcapi.core.offers.factories as offers_factories
from pcapi.core.search.backends import appsearch


pytestmark = pytest.mark.usefixtures("db_session")


def test_serialize():
    pass  # FIXME


def test_do_no_return_booleans():
    # If the backend's `serialize()` method returned boolean values,
    # they would be left as booleans when JSON-encoded, and the App
    # Search API would reject them (because it does not support this
    # data type).

    offer = offers_factories.OfferFactory()
    serialized = appsearch.AppSearchBackend().serialize_offer(offer)
    for key, value in serialized.items():
        assert not isinstance(value, bool), f"Key {key}should not be a boolean"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com/foo/bar", "/foo/bar"),
        ("https://example.com/foo/bar?baz=1", "/foo/bar?baz=1"),
        ("https://example.com/foo/bar?baz=1#quuz", "/foo/bar?baz=1#quuz"),
    ],
)
def test_url_path(url, expected):
    assert appsearch.url_path(url) == expected
