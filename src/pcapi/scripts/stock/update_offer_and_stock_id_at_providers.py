from collections import defaultdict
from typing import List

from sqlalchemy.orm import joinedload

from pcapi.core.bookings.models import Booking
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.models import VenueSQLEntity
from pcapi.repository import repository
from pcapi.utils.logger import logger


BATCH_SIZE = 100


class UpdateOfferSiretException(Exception):
    pass


def update_offer_and_stock_id_at_providers(venue_id: int, old_siret: str, lazy_run: bool = True) -> None:
    """We are looking for two things:
    1) linked offers with the wrong siret. Indeed, when the siret of a venue is changed, linked offers need to be updated
    2) linked offers that have been duplicated by the synchronization process. We want to :
        * deactivate them
        * transfer bookings to the offer with the right siret.
    """

    venue = VenueSQLEntity.query.get(venue_id)
    current_siret = venue.siret

    titelive_offers_with_old_siret = _get_titelive_offers_with_siret_in_id_at_providers(venue, old_siret)
    titelive_offers_with_current_siret = _get_titelive_offers_with_siret_in_id_at_providers(venue, current_siret)
    offers_by_id_at_providers = {offer.idAtProviders: offer for offer in titelive_offers_with_current_siret}

    offers_to_update = []
    stocks_to_update = []
    bookings_to_update = []
    errors = defaultdict(list)
    nb_offers_to_update = len(titelive_offers_with_old_siret)
    nb_updated_offers = 0

    logger.info("%s offers have to be updated", nb_offers_to_update)

    for index, offer_to_update in enumerate(titelive_offers_with_old_siret):
        newIdAtProviders = _update_id_at_provider_siret(offer_to_update.idAtProviders, current_siret)

        # offers have been duplicated for old and current siret.
        # we want to deactivate offers with old siret.
        if newIdAtProviders in offers_by_id_at_providers.keys():
            try:
                valid_offer = offers_by_id_at_providers[newIdAtProviders]
                offer, stocks, bookings = _handle_duplicated_offer(offer_to_update, valid_offer)
                offers_to_update.append(offer)
                if stocks:
                    stocks_to_update.append(*stocks)
                if bookings:
                    bookings_to_update.append(*bookings)

            except UpdateOfferSiretException as e:
                errors[offer_to_update.id].append(e)
                continue

        # offers and stock have a wrong idAtProviders.
        else:
            offer_to_update.idAtProviders = newIdAtProviders
            offers_to_update.append(offer_to_update)
            for stock_to_update in offer_to_update.stocks:
                stock_to_update.idAtProviders = newIdAtProviders
                stocks_to_update.append(stock_to_update)

        if not lazy_run:
            nb_offers_to_update = len(offers_to_update)

            if nb_offers_to_update >= BATCH_SIZE or (
                index == (nb_offers_to_update - 1) and (index % BATCH_SIZE) > 0 or nb_offers_to_update < BATCH_SIZE
            ):
                repository.save(*offers_to_update)
                repository.save(*stocks_to_update)
                repository.save(*bookings_to_update)

                nb_updated_offers += len(offers_to_update)
                offers_to_update = []
                stocks_to_update = []
                bookings_to_update = []

    if lazy_run:
        logger.info("Lazy run, nothing is saved")

    logger.info("%s offers have been updated", nb_updated_offers)
    logger.info("%s offers have encounter some errors", len(errors))
    print("Errors details: ", errors)


def _handle_duplicated_offer(duplicated_offer: Offer, offer: Offer):
    stocks = []
    bookings = []

    duplicated_offer.isActive = False
    for stock_to_update in duplicated_offer.stocks:
        stock_to_update.isSoftDeleted = True
        stocks.append(stock_to_update)
        bookings_to_update = _transfer_bookings(duplicated_offer, stock_to_update, offer)
        if bookings_to_update:
            bookings.append(*bookings_to_update)
    return duplicated_offer, stocks, bookings


def _transfer_bookings(duplicated_offer: Offer, old_stock: Stock, offer: Offer) -> List[Booking]:
    bookings = []
    # _get_transfer_booking_stock_id raise if anything's wrong
    valid_stock = _get_transfer_booking_stock_id(
        duplicated_offer,
        offer.stocks,
        duplicated_offer.id,
        offer.id,
    )

    for booking in old_stock.bookings:
        if valid_stock.remainingQuantity < old_stock.bookingsQuantity:
            raise UpdateOfferSiretException(
                "Unable to transfer bookings from duplicated offer (offerId=%s) to valid offer (offerId=%s). Not enough remaining quantity on the valid stock"
                % (duplicated_offer.id, offer.id)
            )
        if booking.stockId != valid_stock.id:
            booking.stockId = valid_stock.id
            bookings.append(booking)

    return bookings


def _get_titelive_offers_with_siret_in_id_at_providers(venue: VenueSQLEntity, current_siret: str) -> List[Offer]:
    return (
        Offer.query.filter(Offer.venueId == venue.id)
        .filter(Offer.idAtProviders.endswith(current_siret))
        .options(joinedload(Offer.stocks))
        .all()
    )


def _update_id_at_provider_siret(id_at_providers: str, current_siret: str) -> str:
    return id_at_providers.split("@")[0] + "@" + current_siret


def _get_transfer_booking_stock_id(old_stock: Stock, new_stocks: Stock, old_offer_id: str, new_offer_id: str) -> Stock:
    error_params = (
        old_offer_id,
        new_offer_id,
    )

    nb_new_stocks = len(new_stocks)
    if nb_new_stocks == 0:
        raise UpdateOfferSiretException(
            "Unable to transfer bookings from duplicated offer (offerId=%s) to valid offer (offerId=%s). No stock found on the valid offer."
            % error_params
        )
    if nb_new_stocks > 1:
        raise UpdateOfferSiretException(
            "Unable to transfer bookings from duplicated offer (offerId=%s) to valid offer (offerId=%s). More than one stock on the valid offer."
            % error_params
        )

    return new_stocks[0]
