import logging
from typing import Iterable

from flask import current_app
import redis

import pcapi.core.offers.models as offers_models

from . import base


REDIS_OFFER_IDS_TO_INDEX = "search:appsearch:offer-ids-to-index"
REDIS_OFFER_IDS_IN_ERROR_TO_INDEX = "search:appsearch:offer-ids-in-error-to-index"
REDIS_VENUE_IDS_TO_INDEX = "search:appsearch:venue-ids-to-index"
REDIS_INDEXED_OFFER_IDS = "search:appsearch:indexed-offer-ids"

logger = logging.getLogger(__name__)


class AppSearchBackend(base.SearchBackend):
    def __init__(self):
        super().__init__()
        self.appsearch_client = None  # FIXME (dbaty, 2021-06-18)
        self.redis_client = current_app.redis_client

    def enqueue_offer_ids(self, offer_ids: Iterable[int]):
        try:
            self.redis_client.sadd(REDIS_OFFER_IDS_TO_INDEX, *offer_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not add offers to indexation queue", extra={"offers": offer_ids})

    def enqueue_offer_ids_in_error(self, offer_ids: Iterable[int]):
        try:
            self.redis_client.sadd(REDIS_OFFER_IDS_IN_ERROR_TO_INDEX, *offer_ids)
        except redis.exceptions.RedisError:
            logger.exception("Could not add offers to error queue", extra={"offers": offer_ids})

    def enqueue_venue_ids(self, venue_ids: Iterable[int]):
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
        self.appsearch_client.add_documents(documents)
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
        # FIXME (dbaty): remove all indexed documents from App Search.
        # There does not seem to be any way to do that, except by
        # iterating over all indexed documents and removing them.
        try:
            self.redis_client.delete(REDIS_INDEXED_OFFER_IDS)
        except redis.exceptions.RedisError:
            logger.exception("Could not clear indexed offers cache")

    def serialize_offer(self, offer: offers_models.Offer) -> dict:
        return {}  # FIXME (dbaty): that won't do, I am afraid
