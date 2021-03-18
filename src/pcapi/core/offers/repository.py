from datetime import datetime
import math
from typing import Dict
from typing import List
from typing import Optional

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import not_
from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.orm import aliased
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import coalesce

from pcapi.core.bookings.models import Booking
from pcapi.core.offerers.models import Offerer
from pcapi.core.users.models import User
from pcapi.domain.pro_offers.paginated_offers_recap import PaginatedOffersRecap
from pcapi.infrastructure.repository.pro_offers.paginated_offers_recap_domain_converter import to_domain
from pcapi.models import Offer
from pcapi.models import Product
from pcapi.models import Stock
from pcapi.models import UserOfferer
from pcapi.models import Venue
from pcapi.models import db
from pcapi.models.offer_type import ThingType


IMPORTED_CREATION_MODE = "imported"
MANUAL_CREATION_MODE = "manual"

INACTIVE_STATUS = "inactive"
EXPIRED_STATUS = "expired"
SOLD_OUT_STATUS = "soldOut"
ACTIVE_STATUS = "active"


def get_paginated_offers_for_filters(
    user_id: int,
    user_is_admin: bool,
    page: Optional[int],
    offers_per_page: int,
    offerer_id: Optional[int] = None,
    status: Optional[str] = None,
    venue_id: Optional[int] = None,
    type_id: Optional[str] = None,
    name_keywords: Optional[str] = None,
    creation_mode: Optional[str] = None,
    period_beginning_date: Optional[str] = None,
    period_ending_date: Optional[str] = None,
) -> PaginatedOffersRecap:
    query = get_offers_by_filters(
        user_id=user_id,
        user_is_admin=user_is_admin,
        offerer_id=offerer_id,
        status=status,
        venue_id=venue_id,
        type_id=type_id,
        name_keywords=name_keywords,
        creation_mode=creation_mode,
        period_beginning_date=period_beginning_date,
        period_ending_date=period_ending_date,
    )

    query = (
        query.options(joinedload(Offer.venue).joinedload(Venue.managingOfferer))
        .options(joinedload(Offer.stocks).joinedload(Stock.bookings))
        .options(joinedload(Offer.mediations))
        .options(joinedload(Offer.product))
        .order_by(Offer.id.desc())
        .paginate(page, per_page=offers_per_page, error_out=False)
    )

    total_offers = query.total
    total_pages = math.ceil(total_offers / offers_per_page)

    # FIXME (cgaunet, 2020-11-03): we should not have serialization logic in the repository
    return to_domain(
        offers=query.items,
        current_page=query.page,
        total_pages=total_pages,
        total_offers=total_offers,
    )


def get_offers_by_ids(user: User, offer_ids: List[int]) -> Query:
    query = Offer.query
    if not user.isAdmin:
        query = query.join(Venue, Offerer, UserOfferer).filter(
            and_(UserOfferer.userId == user.id, UserOfferer.validationToken.is_(None))
        )
    query = query.filter(Offer.id.in_(offer_ids))
    return query


def get_offers_by_filters(
    user_id: int,
    user_is_admin: bool,
    offerer_id: Optional[int] = None,
    status: Optional[str] = None,
    venue_id: Optional[int] = None,
    type_id: Optional[str] = None,
    name_keywords: Optional[str] = None,
    creation_mode: Optional[str] = None,
    period_beginning_date: Optional[datetime] = None,
    period_ending_date: Optional[datetime] = None,
) -> Query:
    datetime_now = datetime.utcnow()
    query = Offer.query

    if not user_is_admin:
        query = (
            query.join(Venue)
            .join(Offerer)
            .join(UserOfferer)
            .filter(and_(UserOfferer.userId == user_id, UserOfferer.validationToken.is_(None)))
        )
    if offerer_id is not None:
        venue_alias = aliased(Venue)
        query = query.join(venue_alias, Offer.venueId == venue_alias.id).filter(
            venue_alias.managingOffererId == offerer_id
        )
    if venue_id is not None:
        query = query.filter(Offer.venueId == venue_id)
    if creation_mode is not None:
        query = _filter_by_creation_mode(query, creation_mode)
    if type_id is not None:
        query = query.filter(Offer.type == type_id)
    if name_keywords is not None:
        search = name_keywords
        if len(name_keywords) > 3:
            search = "%{}%".format(name_keywords)
        query = query.filter(Offer.name.ilike(search))
    if status is not None:
        query = _filter_by_status(query, datetime_now, status)
    if period_beginning_date is not None or period_ending_date is not None:
        stock_alias = aliased(Stock)
        venue_alias = aliased(Venue)
        query = (
            query.join(stock_alias, Offer.id == stock_alias.offerId)
            .join(venue_alias, Offer.venueId == venue_alias.id)
            .filter(stock_alias.isSoftDeleted.is_(False))
        )
        if period_beginning_date is not None:
            query = query.filter(
                func.timezone(
                    venue_alias.timezone,
                    func.timezone("UTC", stock_alias.beginningDatetime),
                )
                >= period_beginning_date
            )
        if period_ending_date is not None:
            query = query.filter(
                func.timezone(
                    venue_alias.timezone,
                    func.timezone("UTC", stock_alias.beginningDatetime),
                )
                <= period_ending_date
            )

    return query.distinct(Offer.id)


def _filter_by_creation_mode(query: Query, creation_mode: str) -> Query:
    if creation_mode == MANUAL_CREATION_MODE:
        query = query.filter(Offer.lastProviderId.is_(None))
    if creation_mode == IMPORTED_CREATION_MODE:
        query = query.filter(~Offer.lastProviderId.is_(None))

    return query


def _filter_by_status(query: Query, datetime_now: datetime, status: str) -> Query:
    if status == ACTIVE_STATUS:
        query = (
            query.filter(Offer.isActive.is_(True))
            .join(Stock)
            .filter(Stock.isSoftDeleted.is_(False))
            .filter(or_(Stock.bookingLimitDatetime.is_(None), Stock.bookingLimitDatetime >= datetime_now))
            .outerjoin(Booking, and_(Stock.id == Booking.stockId, Booking.isCancelled.is_(False)))
            .group_by(Offer.id, Stock.id)
            .having(
                or_(
                    Stock.quantity.is_(None),
                    Stock.quantity != coalesce(func.sum(Booking.quantity), 0),
                )
            )
        )
    elif status == SOLD_OUT_STATUS:
        query = (
            query.filter(Offer.isActive.is_(True))
            .outerjoin(Stock, and_(Offer.id == Stock.offerId, not_(Stock.isSoftDeleted.is_(True))))
            .filter(or_(Stock.bookingLimitDatetime.is_(None), Stock.bookingLimitDatetime >= datetime_now))
            .filter(or_(Stock.id.is_(None), not_(Stock.quantity.is_(None))))
            .outerjoin(Booking, and_(Stock.id == Booking.stockId, Booking.isCancelled.is_(False)))
            .group_by(Offer.id)
            .having(coalesce(func.sum(Stock.quantity), 0) == coalesce(func.sum(Booking.quantity), 0))
        )
    elif status == EXPIRED_STATUS:
        query = (
            query.filter(Offer.isActive.is_(True))
            .join(Stock)
            .filter(Stock.isSoftDeleted.is_(False))
            .group_by(Offer.id)
            .having(func.max(Stock.bookingLimitDatetime) < datetime_now)
        )
    elif status == INACTIVE_STATUS:
        query = query.filter(Offer.isActive.is_(False))
    return query


def get_stocks_for_offers(offer_ids: List[int]) -> List[Stock]:
    return Stock.query.filter(Stock.offerId.in_(offer_ids)).all()


def get_stocks_for_offer(offer_id: int) -> List[Stock]:
    return (
        Stock.query.options(joinedload(Stock.bookings))
        .filter(Stock.offerId == offer_id)
        .filter(Stock.isSoftDeleted.is_(False))
        .all()
    )


def get_products_map_by_id_at_providers(id_at_providers: List[str]) -> Dict[str, Product]:
    products = (
        Product.query.filter(Product.isGcuCompatible)
        .filter(Product.type == str(ThingType.LIVRE_EDITION))
        .filter(Product.idAtProviders.in_(id_at_providers))
        .all()
    )
    return {product.idAtProviders: product for product in products}


def get_offers_map_by_id_at_providers(id_at_providers: List[str]) -> Dict[str, int]:
    offers_map = {}
    for offer_id, offer_id_at_providers in (
        db.session.query(Offer.id, Offer.idAtProviders).filter(Offer.idAtProviders.in_(id_at_providers)).all()
    ):
        offers_map[offer_id_at_providers] = offer_id

    return offers_map


def get_stocks_by_id_at_providers(id_at_providers: List[str]) -> Dict:
    stocks = (
        Stock.query.filter(Stock.idAtProviders.in_(id_at_providers))
        .outerjoin(Booking, and_(Stock.id == Booking.stockId, Booking.isCancelled.is_(False)))
        .group_by(Stock.id)
        .with_entities(Stock.id, Stock.idAtProviders, coalesce(func.sum(Booking.quantity), 0))
        .all()
    )
    return {
        id_at_providers: {"id": id, "booking_quantity": booking_quantity}
        for (id, id_at_providers, booking_quantity) in stocks
    }


def get_active_offers_count_for_venue(venue_id) -> int:
    datetime_now = datetime.utcnow()
    query = Offer.query.filter(Offer.venueId == venue_id)
    query = _filter_by_status(query, datetime_now, ACTIVE_STATUS)
    return query.distinct(Offer.id).count()


def get_sold_out_offers_count_for_venue(venue_id) -> int:
    datetime_now = datetime.utcnow()
    query = Offer.query.filter(Offer.venueId == venue_id)
    query = _filter_by_status(query, datetime_now, SOLD_OUT_STATUS)
    return query.distinct(Offer.id).count()
