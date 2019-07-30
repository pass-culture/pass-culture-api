""" recommendations stocks """
from typing import List

from domain.departments import get_departement_codes_from_user
from models import Offer
from repository.offer_queries import get_active_offers, order_by_with_criteria
from utils.logger import logger


def get_offers_for_recommendations_discovery(limit=3, user=None) -> List[Offer]:
    if not user or not user.is_authenticated():
        return []

    departement_codes = get_departement_codes_from_user(user)

    offers = get_active_offers(departement_codes=departement_codes,
                               limit=limit,
                               order_by=order_by_with_criteria)

    logger.debug(lambda: '(reco) final offers (events + things) count (%i)',
                 len(offers))

    return offers
