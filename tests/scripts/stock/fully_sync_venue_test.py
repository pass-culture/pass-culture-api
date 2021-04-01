import pytest
import requests_mock

import pcapi.core.bookings.factories as bookings_factories
import pcapi.core.offerers.factories as offerers_factories
import pcapi.core.offers.factories as offers_factories
import pcapi.core.offers.models as offers_models
from pcapi.models.offer_type import ThingType
from pcapi.scripts.stock import fully_sync_venue


@pytest.mark.usefixtures("db_session")
def test_fully_sync_venue():
    api_url = "https://example.com/provider/api"
    provider = offerers_factories.APIProviderFactory(apiUrl=api_url)
    venue_provider = offerers_factories.VenueProviderFactory(provider=provider)
    venue = venue_provider.venue
    stock = offers_factories.StockFactory(quantity=10, offer__venue=venue)
    bookings_factories.BookingFactory(stock=stock)
    product2 = offers_factories.ProductFactory(
        idAtProviders="1234",
        extraData={"prix_livre": 10},
        type=str(ThingType.LIVRE_EDITION),
    )

    with requests_mock.Mocker() as mock:
        response = {
            "total": 1,
            "stocks": [{"ref": "1234", "available": 5}],
        }
        mock.get(f"{api_url}/{venue_provider.venueIdAtOfferProvider}", [{"json": response}, {"json": {"stocks": []}}])
        fully_sync_venue.fully_sync_venue(venue)

    # Check that the quantity of existing stocks has been reset.
    assert stock.quantity == 1
    # Check that offers and stocks have been created or updated.
    offer2 = offers_models.Offer.query.filter_by(product=product2).one()
    assert offer2.stocks[0].quantity == 5


@pytest.mark.usefixtures("db_session")
def test_reset_stock_quantity():
    offer = offers_factories.OfferFactory()
    stock1_no_bookings = offers_factories.StockFactory(offer=offer, quantity=10)
    stock2_only_cancelled_bookings = offers_factories.StockFactory(offer=offer, quantity=10)
    bookings_factories.BookingFactory(stock=stock2_only_cancelled_bookings, isCancelled=True)
    stock3_mix_of_bookings = offers_factories.StockFactory(offer=offer, quantity=10)
    bookings_factories.BookingFactory(stock=stock3_mix_of_bookings)
    bookings_factories.BookingFactory(stock=stock3_mix_of_bookings, isCancelled=True)
    stock4_other_venue = offers_factories.StockFactory(quantity=10)
    venue = offer.venue

    fully_sync_venue._reset_stock_quantity(venue)

    assert stock1_no_bookings.quantity == 0
    assert stock2_only_cancelled_bookings.quantity == 0
    assert stock3_mix_of_bookings.quantity == 1
    assert stock4_other_venue.quantity == 10
