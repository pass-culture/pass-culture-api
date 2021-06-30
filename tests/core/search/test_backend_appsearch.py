import dataclasses

import pytest
import requests_mock

import pcapi.core.offers.factories as offers_factories
from pcapi.core.search.backends import appsearch
from pcapi.core.testing import override_settings


@override_settings()
def get_backend():
    return appsearch.AppSearchBackend()


@dataclasses.dataclass
class FakeOffer:
    id: int


def test_enqueue_offer_ids(app):
    backend = get_backend()
    backend.enqueue_offer_ids([1])
    backend.enqueue_offer_ids({2, 3})
    backend.enqueue_offer_ids([])

    in_queue = app.redis_client.smembers("search:appsearch:offer-ids-to-index")
    assert in_queue == {b"1", b"2", b"3"}


def test_enqueue_offer_ids_in_error(app):
    backend = get_backend()
    backend.enqueue_offer_ids_in_error([1])
    backend.enqueue_offer_ids_in_error({2, 3})
    backend.enqueue_offer_ids_in_error([])

    in_queue = app.redis_client.smembers("search:appsearch:offer-ids-in-error-to-index")
    assert in_queue == {b"1", b"2", b"3"}


def test_enqueue_venue_ids(app):
    backend = get_backend()
    backend.enqueue_venue_ids([1])
    backend.enqueue_venue_ids({2, 3})
    backend.enqueue_venue_ids([])

    in_queue = app.redis_client.smembers("search:appsearch:venue-ids-to-index")
    assert in_queue == {b"1", b"2", b"3"}


def test_pop_offer_ids_from_queue(app):
    backend = get_backend()
    app.redis_client.sadd("search:appsearch:offer-ids-to-index", 1, 2, 3)

    popped = set()
    offer_ids = backend.pop_offer_ids_from_queue(count=2)
    popped |= offer_ids
    assert len(offer_ids) == 2
    assert offer_ids.issubset({1, 2, 3})

    offer_ids = backend.pop_offer_ids_from_queue(count=2)
    popped |= offer_ids
    assert len(offer_ids) == 1
    assert offer_ids.issubset({1, 2, 3})
    assert popped == {1, 2, 3}

    offer_ids = backend.pop_offer_ids_from_queue(count=2)
    assert offer_ids == set()


def test_pop_offer_ids_from_error_queue(app):
    backend = get_backend()
    app.redis_client.sadd("search:appsearch:offer-ids-in-error-to-index", 1, 2, 3)

    popped = set()
    offer_ids = backend.pop_offer_ids_from_queue(count=2, from_error_queue=True)
    popped |= offer_ids
    assert len(offer_ids) == 2
    assert offer_ids.issubset({1, 2, 3})

    offer_ids = backend.pop_offer_ids_from_queue(count=2, from_error_queue=True)
    popped |= offer_ids
    assert len(offer_ids) == 1
    assert offer_ids.issubset({1, 2, 3})
    assert popped == {1, 2, 3}

    offer_ids = backend.pop_offer_ids_from_queue(count=2, from_error_queue=True)
    assert offer_ids == set()


def test_get_venue_ids_from_queue(app):
    backend = get_backend()
    app.redis_client.sadd("search:appsearch:venue-ids-to-index", 1, 2, 3)

    venue_ids = backend.get_venue_ids_from_queue(count=2)
    assert len(venue_ids) == 2
    assert venue_ids.issubset({1, 2, 3})

    # Make sure we did not pop values off the list.
    in_queue = app.redis_client.smembers("search:appsearch:venue-ids-to-index")
    assert in_queue == {b"1", b"2", b"3"}


def test_delete_venue_ids_from_queue(app):
    backend = get_backend()
    app.redis_client.sadd("search:appsearch:venue-ids-to-index", 1, 2, 3)

    backend.delete_venue_ids_from_queue({1, 2})
    in_queue = app.redis_client.smembers("search:appsearch:venue-ids-to-index")
    assert in_queue == {b"3"}


def test_count_offers_to_index_from_queue(app):
    backend = get_backend()
    assert backend.count_offers_to_index_from_queue() == 0
    app.redis_client.sadd("search:appsearch:offer-ids-to-index", 1, 2, 3)
    assert backend.count_offers_to_index_from_queue() == 3


def test_count_offers_to_index_from_error_queue(app):
    backend = get_backend()
    assert backend.count_offers_to_index_from_queue(from_error_queue=True) == 0
    app.redis_client.sadd("search:appsearch:offer-ids-in-error-to-index", 1, 2, 3)
    assert backend.count_offers_to_index_from_queue(from_error_queue=True) == 3


def test_check_offer_is_indexed(app):
    backend = get_backend()
    app.redis_client.sadd("search:appsearch:indexed-offer-ids", "1", "")
    assert backend.check_offer_is_indexed(FakeOffer(id=1))
    assert not backend.check_offer_is_indexed(FakeOffer(id=2))


@pytest.mark.usefixtures("db_session")
def test_index_offers(app):
    backend = get_backend()
    offer = offers_factories.StockFactory().offer
    with requests_mock.Mocker() as mock:
        posted = mock.post("https://fake-id.algolia.net/1/indexes/fake-index/batch", json={})
        backend.index_offers([offer])
        posted_json = posted.last_request.json()
        assert posted_json["requests"][0]["action"] == "updateObject"
        assert posted_json["requests"][0]["body"]["objectID"] == offer.id
    assert backend.check_offer_is_indexed(offer)


def test_unindex_offer_ids(app):
    backend = get_backend()
    app.redis_client.hset("search:appsearch:indexed-offer-ids", "1", "")
    with requests_mock.Mocker() as mock:
        posted = mock.post("https://fake-id.algolia.net/1/indexes/fake-index/batch", json={})
        backend.unindex_offer_ids([1])
        posted_json = posted.last_request.json()
        assert posted_json["requests"][0]["action"] == "deleteObject"
        assert posted_json["requests"][0]["body"]["objectID"] == 1
    assert not backend.check_offer_is_indexed(FakeOffer(id=1))


def test_unindex_all_offers(app):
    backend = get_backend()
    app.redis_client.hset("search:appsearch:indexed-offer-ids", "1", "")
    with requests_mock.Mocker() as mock:
        posted = mock.post("https://fake-id.algolia.net/1/indexes/fake-index/clear", json={})
        backend.unindex_all_offers()
        assert posted.called
    assert not backend.check_offer_is_indexed(FakeOffer(id=1))
