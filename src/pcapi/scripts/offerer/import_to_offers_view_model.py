from datetime import datetime
import logging
from typing import Optional

from sqlalchemy.orm import joinedload

from pcapi.core.offerers.models import Venue
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import OfferValidationStatus
from pcapi.core.offers.models import Stock
from pcapi.core.offers.offer_view_model import OfferViewModel
from pcapi.repository import repository


logger = logging.getLogger(__name__)


def import_to_offers_view_model(offerer_id: int) -> None:
    offers_to_import_count = (
        Offer.query.filter(Offer.validation != OfferValidationStatus.DRAFT)
        .join(Venue)
        .filter(Venue.managingOffererId == offerer_id)
        .count()
    )
    current_page = 0
    offers_per_page = 1000

    while offers_to_import_count > current_page * offers_per_page:
        current_page += 1
        logger.info(
            "Import next page",
            extra={
                "current_page": current_page,
                "offers_per_page": offers_per_page,
                "offers_to_import_count": offers_to_import_count,
            },
        )
        _batch_import(offerer_id, current_page, offers_per_page)


def _batch_import(offerer_id: int, page: int, offers_per_page: int) -> None:
    offers_to_import = (
        Offer.query.filter(Offer.validation != OfferValidationStatus.DRAFT)
        .options(joinedload(Offer.venue).joinedload(Venue.managingOfferer))
        .options(joinedload(Offer.stocks))
        .options(joinedload(Offer.mediations))
        .options(joinedload(Offer.product))
        .join(Venue)
        .filter(Venue.managingOffererId == offerer_id)
        .order_by(Offer.id.desc())
        .paginate(page, per_page=offers_per_page, error_out=False)
    )

    offer_view_models = []

    for offer in offers_to_import.items:
        offer_view_models.append(_build_offer_view_model(offer))

    repository.save(*offer_view_models)


def _build_offer_view_model(offer: Offer) -> OfferViewModel:
    offer_stocks = offer.activeStocks

    offer_view_model = OfferViewModel()
    offer_view_model.id = offer.id
    offer_view_model.isActive = offer.isActive
    offer_view_model.isEditable = offer.isEditable
    offer_view_model.hasBookingLimitDatetimesPassed = offer.hasBookingLimitDatetimesPassed
    offer_view_model.isEvent = offer.isEvent
    offer_view_model.isThing = offer.isThing
    offer_view_model.creationMode = "manual" if offer.lastProviderId is None else "imported"
    offer_view_model.remainingStockQuantity = _compute_remaining_stock_quantity(offer_stocks)
    offer_view_model.stocksCount = len(offer_stocks)
    offer_view_model.soldOutStocksCount = _compute_sold_out_stocks(offer_stocks)
    offer_view_model.firstEventDatetime = _get_first_event_datetime(offer_stocks) if offer.isEvent else None
    offer_view_model.lastEventDatetime = _get_last_event_datetime(offer_stocks) if offer.isEvent else None
    offer_view_model.name = offer.name
    offer_view_model.thumbUrl = offer.thumbUrl
    offer_view_model.status = offer.status.name
    offer_view_model.timezone = offer.venue.timezone
    offer_view_model.type = offer.type
    offer_view_model.venueId = offer.venueId
    offer_view_model.venueName = offer.venue.name
    offer_view_model.venueTimezone = offer.venue.timezone
    offer_view_model.venuePublicName = offer.venue.publicName
    offer_view_model.venueDepartementCode = offer.venue.departementCode
    offer_view_model.venueIsVirtual = offer.venue.isVirtual
    offer_view_model.offererId = offer.venue.managingOffererId
    offer_view_model.offererName = offer.venue.managingOfferer.name

    return offer_view_model


def _get_first_event_datetime(stocks: list[Stock]) -> Optional[datetime]:
    if len(stocks) == 0:
        return None
    return min([stock.beginningDatetime for stock in stocks])


def _get_last_event_datetime(stocks: list[Stock]) -> Optional[datetime]:
    if len(stocks) == 0:
        return None
    return max([stock.beginningDatetime for stock in stocks])


def _compute_remaining_stock_quantity(stocks: list[Stock]):
    stocks_remaining_quantities = [stock.remainingQuantity for stock in stocks]
    if "unlimited" in stocks_remaining_quantities:
        return "unlimited"

    return sum(stocks_remaining_quantities)


def _compute_sold_out_stocks(stocks: list[Stock]) -> int:
    return len([stock.remainingQuantity for stock in stocks if stock.remainingQuantity == 0])
