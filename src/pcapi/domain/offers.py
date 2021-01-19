from typing import List

from pcapi.core.offers.models import Offer


def update_is_active_status(offers: List[Offer], status: bool) -> List[Offer]:
    for offer in offers:
        offer.isActive = status

    return offers
