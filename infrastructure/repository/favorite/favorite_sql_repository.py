from typing import List, Dict

from sqlalchemy.orm import joinedload, selectinload

from domain.favorite.favorite import Favorite
from domain.favorite.favorite_repository import FavoriteRepository
from infrastructure.repository.favorite import favorite_domain_converter
from models import FavoriteSQLEntity, OfferSQLEntity, StockSQLEntity, VenueSQLEntity, BookingSQLEntity


class FavoriteSQLRepository(FavoriteRepository):
    def find_by_beneficiary(self, beneficiary_identifier: int) -> List[Favorite]:
        favorite_sql_entities = FavoriteSQLEntity.query \
            .filter(FavoriteSQLEntity.userId == beneficiary_identifier) \
            .options(
                selectinload(FavoriteSQLEntity.offer)
                    .joinedload(OfferSQLEntity.venue)
                    .joinedload(VenueSQLEntity.managingOfferer)
             ) \
            .options(
                selectinload(FavoriteSQLEntity.mediation)
            ) \
            .options(
                selectinload(FavoriteSQLEntity.offer)
                    .joinedload(OfferSQLEntity.stocks)
            ) \
            .options(
                selectinload(FavoriteSQLEntity.offer)
                    .joinedload(OfferSQLEntity.product)
            ) \
            .options(
                selectinload(FavoriteSQLEntity.offer)
                    .joinedload(OfferSQLEntity.mediations)
            ) \
            .all()

        offer_ids = [favorite_sql_entity.offer.id for favorite_sql_entity in favorite_sql_entities]

        bookings = OfferSQLEntity.query \
            .filter(OfferSQLEntity.id.in_(offer_ids)) \
            .join(StockSQLEntity) \
            .join(BookingSQLEntity) \
            .filter(BookingSQLEntity.userId == beneficiary_identifier) \
            .filter(BookingSQLEntity.isCancelled == False) \
            .with_entities(
                BookingSQLEntity.id.label('booking_id'),
                OfferSQLEntity.id.label('offer_id'),
                StockSQLEntity.id.label('stock_id')
        ) \
            .all()

        bookings_by_offer_id = {booking.offer_id: {'id': booking.booking_id, 'stock_id': booking.stock_id} for booking in bookings}

        return [favorite_domain_converter.to_domain(favorite_sql_entity, bookings_by_offer_id.get(favorite_sql_entity.offerId, None)) for favorite_sql_entity in
                favorite_sql_entities]
