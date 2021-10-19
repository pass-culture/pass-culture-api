from pcapi import settings
from pcapi.core import search
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import OfferValidationStatus
from pcapi.core.offers.models import Stock
from pcapi.models.db import db


BATCH_SIZE = 10000


def reject_thing_offers_from_price_limit(price_limit) -> None:
    stock_offer_ids = (
        Stock.query.filter(Stock.isSoftDeleted == False, Stock.beginningDatetime == None, Stock.price > price_limit)
        .with_entities(Stock.offerId)
        .all()
    )

    number_of_stock_offers = len(stock_offer_ids)
    print(f"{number_of_stock_offers} stocks with price over {price_limit}€ found.")

    rejected_offer_ids = []
    for current_start_index in range(0, number_of_stock_offers, BATCH_SIZE):
        stock_offer_ids_batch = stock_offer_ids[
            current_start_index : min(current_start_index + BATCH_SIZE, number_of_stock_offers)
        ]
        query_to_update = Offer.query.filter(
            Offer.id.in_(stock_offer_ids_batch),
            Offer.isSoftDeleted == False,
            Offer.isEducational == False,
        )
        query_to_update.update(
            {
                "isActive": False,
                "validation": OfferValidationStatus.REJECTED,
            },
            synchronize_session=False,
        )

        db.session.commit()

        batch_rejected_offer_ids = query_to_update.with_entities(Offer.id)
        print(f"{len(batch_rejected_offer_ids)} offer have been rejected.")
        rejected_offer_ids += batch_rejected_offer_ids

    unindex_batch_size = settings.ALGOLIA_DELETING_OFFERS_CHUNK_SIZE
    nb_offer_to_unindex = len(rejected_offer_ids)
    for current_start_index in range(0, nb_offer_to_unindex, unindex_batch_size):
        unindex_offer_ids = rejected_offer_ids[
            current_start_index : min(current_start_index + unindex_batch_size, nb_offer_to_unindex)
        ]
        search.unindex_offer_ids(unindex_offer_ids)
        print(f"{len(unindex_offer_ids)} offer have been unindex.")
