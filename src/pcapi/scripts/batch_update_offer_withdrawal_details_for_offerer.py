"""
Fetch offers from database and update their date updated on Batch.
"""
import math

from sqlalchemy import func

from pcapi.core.offers.models import Offer
from pcapi.models import db


def batch_update_offer_date_update(batch_size: int = 1000) -> None:
    min_id = db.session.query(func.min(Offer.id)).scalar()
    max_id = db.session.query(func.max(Offer.id)).scalar()
    number_of_batch = math.ceil(max_id / batch_size)
    number_of_batch_done = 0
    ranges = [(i, i + batch_size) for i in range(min_id, max_id + 1, batch_size)]
    for start, end in ranges:
        db.session.execute(
            """
            UPDATE offer
            SET "dateUpdated" = '2021-09-06 09:00:00'
            WHERE
              offer.id BETWEEN :start AND :end
              AND offer."dateUpdated" IS NULL
            """,
            {"start": start, "end": end},
        )
        db.session.commit()
        number_of_batch_done += 1
        print("Offer details update ongoing... batch %s of %s" % (number_of_batch_done, number_of_batch))
