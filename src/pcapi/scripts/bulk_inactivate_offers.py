import logging
from typing import Iterable

from pcapi.algolia.usecase.orchestrator import _process_deleting
from pcapi.core.offers.models import Offer
from pcapi.flask_app import app
from pcapi.models.db import db
from pcapi.models.feature import FeatureToggle
from pcapi.repository import feature_queries


logger = logging.getLogger(__name__)


def process_batch(offer_ids: list[str], synchronize_algolia: bool) -> None:
    logger.info("Bulk-deactivating offers as incompatible", extra={"offers": offer_ids})
    offers = Offer.query.filter(Offer.id.in_(offer_ids))
    offer_ids_list = [offer_id for offer_id, in offers.with_entities(Offer.id)]
    offers.update({"isActive": False}, synchronize_session=False)
    db.session.commit()
    if synchronize_algolia:
        _process_deleting(app.redis_client, offer_ids_list)


def bulk_inactivate_offers(iterable: Iterable[str], batch_size: int) -> None:
    total = 0
    batch = []
    synchronize_algolia = feature_queries.is_active(FeatureToggle.SYNCHRONIZE_ALGOLIA)

    for line in iterable:
        offer_id = line.strip()
        batch.append(offer_id)
        total += 1
        if len(batch) == batch_size:
            process_batch(batch, synchronize_algolia)
            batch = []
            print("Count: %i", total)
    process_batch(batch, synchronize_algolia)
    print("Count: %i", total)


def bulk_mark_incompatible_from_path(path: str, batch_size: int) -> None:
    with open(path) as fp:
        return bulk_inactivate_offers(fp, batch_size)
