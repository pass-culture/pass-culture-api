from datetime import datetime

from sqlalchemy import Sequence

from pcapi.core.bookings.repository import count_not_cancelled_bookings_quantity_by_stock_id
from pcapi.core.providers.models import VenueProvider
from pcapi.local_providers.local_provider import LocalProvider
from pcapi.local_providers.providable_info import ProvidableInfo
from pcapi.models import Offer
from pcapi.models import Stock
from pcapi.models.db import Model
from pcapi.models.db import db
from pcapi.repository import product_queries


class GenericStocks(LocalProvider):
    # The following attributes MUST be overriden by subclasses
    name = None
    get_provider_stock_information = None  # must be overriden by subclasses
    # The following attributes MAY be overriden by subclasses
    can_create = True
    price_divider_to_euro = None

    def __init__(
        self,
        venue_provider: VenueProvider,
        **options,
    ):
        super().__init__(venue_provider, **options)
        self.venue = venue_provider.venue
        self.id_at_provider = self.venue_provider.venueIdAtOfferProvider
        self.last_processed_isbn = ""
        self.stock_data = iter([])
        self.modified_since = venue_provider.lastSyncDate
        self.product = None
        self.offer_id = None

    def __next__(self) -> list[ProvidableInfo]:
        try:
            self.provider_stocks = next(self.stock_data)
        except StopIteration:
            self.stock_data = self.get_provider_stock_information(  # pylint: disable=not-callable
                self.id_at_provider, self.last_processed_isbn, self.modified_since
            )
            self.provider_stocks = next(self.stock_data)

        self.last_processed_isbn = str(self.provider_stocks["ref"])
        # FIXME: This line create a lot of read queries on the database which slows the process very much.
        self.product = product_queries.find_active_book_product_by_isbn(self.provider_stocks["ref"])
        if not self.product:
            return []

        providable_info_offer = self.create_providable_info(
            Offer, f"{self.provider_stocks['ref']}@{self.id_at_provider}", datetime.utcnow()
        )
        providable_info_stock = self.create_providable_info(
            Stock, f"{self.provider_stocks['ref']}@{self.id_at_provider}", datetime.utcnow()
        )

        return [providable_info_offer, providable_info_stock]

    def fill_object_attributes(self, pc_object: Model) -> None:
        if isinstance(pc_object, Offer):
            self.fill_offer_attributes(pc_object)
        if isinstance(pc_object, Stock):
            self.fill_stock_attributes(pc_object)

    def fill_offer_attributes(self, offer: Offer) -> None:
        offer.bookingEmail = self.venue.bookingEmail
        offer.description = self.product.description
        offer.extraData = self.product.extraData
        offer.name = self.product.name
        offer.productId = self.product.id
        offer.venueId = self.venue.id
        offer.type = self.product.type

        is_new_offer_to_create = not offer.id
        if is_new_offer_to_create:
            next_id = self.get_next_offer_id_from_sequence()
            offer.id = next_id

        self.offer_id = offer.id

    def fill_stock_attributes(self, stock: Stock) -> None:
        bookings_quantity = count_not_cancelled_bookings_quantity_by_stock_id(stock.id)
        stock.quantity = self.provider_stocks["available"] + bookings_quantity
        stock.bookingLimitDatetime = None
        stock.offerId = self.offer_id
        if self.provider_stocks["price"] and self.price_divider_to_euro:
            stock.price = int(self.provider_stocks["price"]) / self.price_divider_to_euro
        else:
            # Beware: price may be None. repository.save() will catch and skip the stock
            stock.price = self.provider_stocks["price"]
        stock.dateModified = datetime.now()

    @staticmethod
    def get_next_offer_id_from_sequence():
        sequence = Sequence("offer_id_seq")
        return db.session.execute(sequence)
