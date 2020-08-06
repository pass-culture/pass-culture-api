from datetime import datetime
from typing import List, Callable

from sqlalchemy import func

from models import OfferSQLEntity, StockSQLEntity
from models.db import db
from repository import repository


def get_offers_with_max_stock_date_between_today_and_end_of_quarantine(first_day_after_quarantine: datetime,
                                                                       today: datetime) -> List[OfferSQLEntity]:
    quarantine_offers_query = build_query_offers_with_max_stock_date_between_today_and_end_of_quarantine(
        first_day_after_quarantine, today)
    return quarantine_offers_query.all()


def build_query_offers_with_max_stock_date_between_today_and_end_of_quarantine(first_day_after_quarantine, today):
    stock_with_latest_date_by_offer = db.session.query(
        StockSQLEntity.offerId,
        func.max(StockSQLEntity.beginningDatetime).label('beginningDatetime')
    ) \
        .group_by(StockSQLEntity.offerId).subquery()
    quarantine_offers_query = OfferSQLEntity.query.join(stock_with_latest_date_by_offer,
                                                        OfferSQLEntity.id == stock_with_latest_date_by_offer.c.offerId).filter(
        stock_with_latest_date_by_offer.c.beginningDatetime < first_day_after_quarantine).filter(
        stock_with_latest_date_by_offer.c.beginningDatetime > today)
    return quarantine_offers_query


def deactivate_offers(offers: List[OfferSQLEntity]):
    for offer in offers:
        offer.isActive = False
    repository.save(*offers)


def deactivate_offers_with_max_stock_date_between_today_and_end_of_quarantine(first_day_after_quarantine: datetime,
                                                                              today: datetime,
                                                                              get_offers: Callable = get_offers_with_max_stock_date_between_today_and_end_of_quarantine):
    offers = get_offers(first_day_after_quarantine, today)
    deactivate_offers(offers)
