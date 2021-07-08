import datetime
import decimal
import json
import logging
from typing import Iterable
import urllib.parse

from flask import current_app
import redis

from pcapi import settings
import pcapi.core.offers.models as offers_models
from pcapi.utils import requests
import pcapi.utils.date as date_utils

from . import base


REDIS_OFFER_IDS_TO_INDEX = "search:appsearch:offer-ids-to-index"
REDIS_OFFER_IDS_IN_ERROR_TO_INDEX = "search:appsearch:offer-ids-in-error-to-index"
REDIS_VENUE_IDS_TO_INDEX = "search:appsearch:venue-ids-to-index"
REDIS_INDEXED_OFFER_IDS = "search:appsearch:indexed-offer-ids"

ENGINE_NAME = "offers"
ENGINE_LANGUAGE = None
# The App Search API accepts up to 100 documents per request
# (https://www.elastic.co/guide/en/app-search/current/documents.html#documents-create).
DOCUMENTS_PER_REQUEST_LIMIT = 100


SCHEMA = {
    "artist": "text",
    "category": "text",
    "date_created": "date",
    "dates": "number",  # easier to work with as a number in the frontend
    "description": "text",
    "is_digital": "number",
    "is_duo": "number",
    "is_educational": "number",
    "is_event": "number",
    "is_thing": "number",
    "isbn": "text",
    "label": "text",
    "name": "text",
    # "id": "number",  must not be provided when creating the schema.
    "prices": "number",
    "ranking_weight": "number",
    "stocks_date_created": "number",  # easier to work with as a number in the frontend
    "tags": "text",
    "times": "number",
    "thumb_url": "text",
    "type": "text",
    "offerer_name": "text",
    "venue_city": "text",
    "venue_department_code": "text",
    "venue_name": "text",
    "venue_position": "geolocation",
    "venue_public_name": "text",
}


logger = logging.getLogger(__name__)


def url_path(url):
    """Return the path component of a URL.

    Example::

        >>> url_path("https://example.com/foo/bar/baz?a=1")
        "/foo/bar/baz?a=1"
    """
    if not url:
        return None
    parts = urllib.parse.urlparse(url)
    path = parts.path
    if parts.query:
        path += f"?{parts.query}"
    if parts.fragment:
        path += f"#{parts.fragment}"
    return path


class AppSearchBackend(base.SearchBackend):
    def __init__(self):
        super().__init__()
        self.appsearch_client = AppSearchApiClient(host=settings.APPSEARCH_HOST, api_key=settings.APPSEARCH_API_KEY)
        self.redis_client = current_app.redis_client

    def enqueue_offer_ids(self, offer_ids: Iterable[int]):
        if not offer_ids:
            return
        try:
            self.redis_client.sadd(REDIS_OFFER_IDS_TO_INDEX, *offer_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not add offers to indexation queue", extra={"offers": offer_ids})

    def enqueue_offer_ids_in_error(self, offer_ids: Iterable[int]):
        if not offer_ids:
            return
        try:
            self.redis_client.sadd(REDIS_OFFER_IDS_IN_ERROR_TO_INDEX, *offer_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not add offers to error queue", extra={"offers": offer_ids})

    def enqueue_venue_ids(self, venue_ids: Iterable[int]):
        if not venue_ids:
            return
        try:
            self.redis_client.sadd(REDIS_VENUE_IDS_TO_INDEX, *venue_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not add venues to indexation queue", extra={"venues": venue_ids})

    def pop_offer_ids_from_queue(self, count: int, from_error_queue: bool = False) -> set[int]:
        if from_error_queue:
            redis_set_name = REDIS_OFFER_IDS_IN_ERROR_TO_INDEX
        else:
            redis_set_name = REDIS_OFFER_IDS_TO_INDEX

        try:
            offer_ids = self.redis_client.spop(redis_set_name, count)
            return {int(offer_id) for offer_id in offer_ids}  # str -> int
        except redis.exceptions.RedisError:
            logger.exception("Could not pop offer ids to index from queue")
            return []

    def get_venue_ids_from_queue(self, count: int) -> set[int]:
        try:
            venue_ids = self.redis_client.srandmember(REDIS_VENUE_IDS_TO_INDEX, count)
            return {int(venue_id) for venue_id in venue_ids}  # str -> int
        except redis.exceptions.RedisError:
            logger.exception("Could not get venue ids to index from queue")
            return set()

    def delete_venue_ids_from_queue(self, venue_ids: Iterable[int]) -> None:
        if not venue_ids:
            return
        try:
            self.redis_client.srem(REDIS_VENUE_IDS_TO_INDEX, *venue_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not delete indexed venue ids from queue")

    def count_offers_to_index_from_queue(self, from_error_queue: bool = False) -> int:
        if from_error_queue:
            redis_set_name = REDIS_OFFER_IDS_IN_ERROR_TO_INDEX
        else:
            redis_set_name = REDIS_OFFER_IDS_TO_INDEX

        try:
            return self.redis_client.scard(redis_set_name)
        except redis.exceptions.RedisError:
            logger.exception("Could not count offers left to index from queue")
            return 0

    def check_offer_is_indexed(self, offer: offers_models.Offer) -> bool:
        try:
            return self.redis_client.sismember(REDIS_INDEXED_OFFER_IDS, offer.id)
        except redis.exceptions.RedisError:
            logger.exception("Could not check whether offer exists in cache", extra={"offer": offer.id})
            # This function is only used to avoid an unnecessary
            # deletion request to App Search if the offer is not in
            # the cache. Here we don't know, so we'll say it's in the
            # cache so that we do perform a request to App Search.
            return True

    def index_offers(self, offers: Iterable[offers_models.Offer]) -> None:
        if not offers:
            return
        documents = [self.serialize_offer(offer) for offer in offers]
        self.appsearch_client.create_or_update_documents(documents)
        offer_ids = [offer.id for offer in offers]
        try:
            self.redis_client.sadd(REDIS_INDEXED_OFFER_IDS, *offer_ids)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Could not add to list of indexed offers", extra={"offers": offer_ids})

    def unindex_offer_ids(self, offer_ids: Iterable[int]) -> None:
        if not offer_ids:
            return
        self.appsearch_client.delete_documents(offer_ids)
        try:
            self.redis_client.srem(REDIS_INDEXED_OFFER_IDS, *offer_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not remove offers from indexed offers set", extra={"offers": offer_ids})

    def unindex_all_offers(self) -> None:
        # FIXME (dbaty): remove all indexed documents from the engine.
        # There does not seem to be any way to do that, except by
        # iterating over all indexed documents and removing them.
        try:
            self.redis_client.delete(REDIS_INDEXED_OFFER_IDS)
        except redis.exceptions.RedisError:
            logger.exception("Could not clear indexed offers cache")

    def serialize_offer(self, offer: offers_models.Offer) -> dict:
        dates = []
        times = []
        if offer.isEvent:
            dates = [stock.beginningDatetime.timestamp() for stock in offer.bookableStocks]
            times = [
                date_utils.get_time_in_seconds_from_datetime(stock.beginningDatetime) for stock in offer.bookableStocks
            ]

        extra_data = offer.extraData or {}
        # FIXME (dbaty): see Cyril's original note about that in `AlgoliaBackend.serialize_offer()`
        isbn = (extra_data.get("isbn") or extra_data.get("visa")) if extra_data else None

        artist = " ".join(extra_data.get(key, "") for key in ("author", "performer", "speaker", "stageDirector"))

        venue = offer.venue
        if venue.longitude is not None and venue.latitude is not None:
            position = [venue.longitude, venue.latitude]
        else:
            position = None

        return {
            "artist": artist,
            "category": offer.offer_category_name_for_app,
            "date_created": offer.dateCreated,  # used only to rank results
            "dates": dates,
            "description": offer.description,
            # TODO (antoinewg, 2021-07-02): remove fields once we've migrated completely to App Search.
            # isDigital is used by the frontend to not show the fake geoloc for digital offers used by algolia
            # Since we don't fake geoloc on App Search => we don't need it
            "is_digital": int(offer.isDigital),
            "is_duo": int(offer.isDuo),
            "is_educational": False,
            "is_event": int(offer.isEvent),
            "is_thing": int(offer.isThing),
            "isbn": isbn,
            "label": offer.offerType["appLabel"],
            "name": offer.name,
            "id": offer.id,
            "prices": [int(stock.price * 100) for stock in offer.bookableStocks],
            "ranking_weight": offer.rankingWeight or 0,
            "stocks_date_created": [stock.dateCreated.timestamp() for stock in offer.bookableStocks],
            "tags": [criterion.name for criterion in offer.criteria],
            "times": times,
            "thumb_url": url_path(offer.thumbUrl),
            "type": offer.offerType["sublabel"],
            "offerer_name": venue.managingOfferer.name,
            "venue_city": venue.city,
            "venue_department_code": venue.departementCode,
            "venue_name": venue.name,
            "venue_position": position,
            "venue_public_name": venue.publicName,
        }


class AppSearchApiClient:
    def __init__(self, host: str, api_key: str):
        self.host = host
        self.api_key = api_key

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    # Engines API: https://www.elastic.co/guide/en/app-search/current/engines.html
    @property
    def engines_url(self):
        path = "/api/as/v1/engines"
        return f"{self.host.rstrip('/')}{path}"

    def create_engine(self):
        data = {"name": ENGINE_NAME, "language": ENGINE_LANGUAGE}
        response = requests.post(self.engines_url, headers=self.headers, json=data)
        return response

    # Schema API: https://www.elastic.co/guide/en/app-search/current/schema.html
    @property
    def schema_url(self):
        path = f"/api/as/v1/engines/{ENGINE_NAME}/schema"
        return f"{self.host.rstrip('/')}{path}"

    def update_schema(self):
        response = requests.post(self.schema_url, headers=self.headers, json=SCHEMA)
        return response

    # Documents API: https://www.elastic.co/guide/en/app-search/current/documents.html
    @property
    def documents_url(self):
        path = f"/api/as/v1/engines/{ENGINE_NAME}/documents"
        return f"{self.host.rstrip('/')}{path}"

    def create_or_update_documents(self, documents: Iterable[dict]):
        batches = [
            documents[i : i + DOCUMENTS_PER_REQUEST_LIMIT]
            for i in range(0, len(documents), DOCUMENTS_PER_REQUEST_LIMIT)
        ]
        # Error handling is done by the caller.
        for batch in batches:
            data = json.dumps(batch, cls=AppSearchJsonEncoder)
            response = requests.post(self.documents_url, headers=self.headers, data=data)
            response.raise_for_status()
            # Except here when App Search returns a 200 OK response
            # even if *some* documents cannot be processed. In that
            # case we log it here. It denotes a bug on our side: type
            # mismatch on a field, bogus JSON serialization, etc.
            response_data = response.json()
            errors = [item for item in response_data if item["errors"]]
            if errors:
                logger.error("Some offers could not be indexed, possible typing bug", extra={"errors": errors})

    def delete_documents(self, offer_ids: Iterable[int]):
        # Error handling is done by the caller.
        data = json.dumps(offer_ids)
        response = requests.delete(self.documents_url, headers=self.headers, data=data)
        response.raise_for_status()


class AppSearchJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat().split(".")[0] + "Z"
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)
