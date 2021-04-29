from datetime import datetime
import math
from typing import Optional

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.orm import Query

from pcapi.core.offers.models import OfferStatus
from pcapi.core.offers.offer_view_model import OfferViewModel
from pcapi.domain.identifier.identifier import Identifier
from pcapi.domain.pro_offers.paginated_offers_recap import OfferRecap
from pcapi.domain.pro_offers.paginated_offers_recap import PaginatedOffersRecap
from pcapi.models import UserOfferer


IMPORTED_CREATION_MODE = "imported"
MANUAL_CREATION_MODE = "manual"


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

    query = query.order_by(OfferViewModel.id.desc()).paginate(page, per_page=offers_per_page, error_out=False)

    total_offers = query.total
    total_pages = math.ceil(total_offers / offers_per_page)

    # FIXME (cgaunet, 2020-11-03): we should not have serialization logic in the repository
    return _to_domain(
        offers=query.items,
        current_page=query.page,
        total_pages=total_pages,
        total_offers=total_offers,
    )


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
    query = OfferViewModel.query

    if not user_is_admin:
        query = query.join(UserOfferer, UserOfferer.offererId == OfferViewModel.offererId).filter(
            and_(UserOfferer.userId == user_id, UserOfferer.validationToken.is_(None))
        )
    if offerer_id is not None:
        query = query.filter(OfferViewModel.offererId == offerer_id)
    if venue_id is not None:
        query = query.filter(OfferViewModel.venueId == venue_id)
    if creation_mode is not None:
        query = _filter_by_creation_mode(query, creation_mode)
    if type_id is not None:
        query = query.filter(OfferViewModel.type == type_id)
    if name_keywords is not None:
        search = name_keywords
        if len(name_keywords) > 3:
            search = "%{}%".format(name_keywords)
        query = query.filter(OfferViewModel.name.ilike(search))
    if status is not None:
        query = _filter_by_status(query, status)
    if period_beginning_date is not None or period_ending_date is not None:
        if period_beginning_date is not None:
            query = query.filter(
                func.timezone(
                    OfferViewModel.timezone,
                    func.timezone("UTC", OfferViewModel.firstEventDatetime),
                )
                >= period_beginning_date
            )
        if period_ending_date is not None:
            query = query.filter(
                func.timezone(
                    OfferViewModel.timezone,
                    func.timezone("UTC", OfferViewModel.lastEventDatetime),
                )
                <= period_ending_date
            )

    return query


def _filter_by_creation_mode(query: Query, creation_mode: str) -> Query:
    return query.filter(OfferViewModel.creationMode == creation_mode)


def _filter_by_status(query: Query, status: str) -> Query:
    return query.filter(OfferViewModel.status == OfferStatus[status].name)


def _to_domain(
    offers: [OfferViewModel], current_page: int, total_pages: int, total_offers: int
) -> PaginatedOffersRecap:
    offers_recap = [_offer_recap_to_domain(offer) for offer in offers]

    return PaginatedOffersRecap(
        offers_recap=offers_recap, current_page=current_page, total_pages=total_pages, total_offers=total_offers
    )


def _offer_recap_to_domain(offer: OfferViewModel) -> OfferRecap:
    stocks = _stock_serializer(offer)

    return OfferRecap(
        identifier=Identifier(offer.id),
        has_booking_limit_datetimes_passed=offer.hasBookingLimitDatetimesPassed,
        is_active=offer.isActive,
        is_editable=offer.isEditable,
        is_event=offer.isEvent,
        is_thing=offer.isThing,
        name=offer.name,
        thumb_url=offer.thumbUrl,
        offer_type=offer.type,
        venue_identifier=Identifier(offer.venueId),
        venue_is_virtual=offer.venueIsVirtual,
        venue_managing_offerer_id=offer.offererId,
        venue_name=offer.venueName,
        venue_offerer_name=offer.offererName,
        venue_public_name=offer.venuePublicName,
        venue_departement_code=offer.venueDepartementCode,
        stocks=stocks,
        status=offer.status,
    )


def _stock_serializer(offer: OfferViewModel) -> [dict]:
    stocks = []
    stock_count = 0
    stock_quantity = 0

    while offer.soldOutStocksCount > stock_count:
        stock_count += 1
        sold_out_stock = {
            "identifier": Identifier(stock_count),
            "has_booking_limit_datetime_passed": False,
            "remaining_quantity": 0,
        }
        stocks.append(sold_out_stock)

    while offer.stocksCount > stock_count:
        stock_count = stock_count + 1
        stock = {
            "identifier": Identifier(stock_count),
            "has_booking_limit_datetime_passed": False,
            "remaining_quantity": offer.remainingStockQuantity - stock_quantity
            if stock_count == offer.stocksCount
            else 1,
        }
        stock_quantity += stock["remaining_quantity"]
        stocks.append(stock)

    return stocks
