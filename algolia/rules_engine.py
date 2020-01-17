from models import Offer


def is_eligible_for_indexing(offer: Offer) -> bool:
    if offer is None:
        return False

    venue = offer.venue
    offerer = venue.managingOfferer

    if offerer.isActive \
            and offerer.validationToken is None \
            and offer.isActive \
            and offer.has_enough_stock_to_be_booked() \
            and venue.validationToken is None:
        return True

    return False
