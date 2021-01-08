from unittest.mock import call
from unittest.mock import patch

import pytest

from pcapi.core.bookings.factories import BookingFactory
from pcapi.core.offers.factories import OfferFactory
from pcapi.core.offers.factories import StockFactory
from pcapi.core.offers.factories import VenueFactory
from pcapi.repository import repository
from pcapi.scripts.stock.update_offer_and_stock_id_at_providers import (
    _get_titelive_offers_with_siret_in_id_at_providers,
)
from pcapi.scripts.stock.update_offer_and_stock_id_at_providers import _update_id_at_provider_siret
from pcapi.scripts.stock.update_offer_and_stock_id_at_providers import update_offer_and_stock_id_at_providers


class UpdateOfferAndStockIdAtProvidersTest:
    @patch("pcapi.scripts.stock.update_offer_and_stock_id_at_providers.repository")
    @pytest.mark.usefixtures("db_session")
    def should_update_id_at_providers_for_offers_and_stocks_with_current_siret(self, mock_repository, app):
        # Given
        old_siret = "85234081900014"
        current_siret = "32363560700019"
        venue = VenueFactory(siret=current_siret, id=12)
        offer = OfferFactory(venue=venue, idAtProviders=f"9782742785988@{old_siret}")
        stock = StockFactory(offer=offer, idAtProviders=f"9782742785988@{old_siret}")
        repository.save(stock)

        # When
        update_offer_and_stock_id_at_providers(venue_id=venue.id, old_siret=old_siret, lazy_run=False)

        # Then
        assert offer.idAtProviders == f"9782742785988@{current_siret}"
        assert stock.idAtProviders == f"9782742785988@{current_siret}"
        assert mock_repository.save.call_count == 3
        assert mock_repository.save.call_args_list == [call(offer), call(stock), call()]

    @patch("pcapi.scripts.stock.update_offer_and_stock_id_at_providers.repository")
    @pytest.mark.usefixtures("db_session")
    def should_soft_delete_offer_and_stock_when_new_id_at_providers_offer_already_exist(self, mock_repository, app):
        # Given
        old_siret = "85234081900014"
        current_siret = "32363560700019"
        venue = VenueFactory(siret=current_siret, id=12)
        offer = OfferFactory(venue=venue, idAtProviders=f"9782742785988@{old_siret}")
        new_offer = OfferFactory(venue=venue, idAtProviders=f"9782742785988@{current_siret}")
        stock = StockFactory(offer=offer, idAtProviders=f"9782742785988@{old_siret}")
        new_stock = StockFactory(offer=new_offer, idAtProviders=f"9782742785988@{current_siret}")

        repository.save(stock, new_stock)

        # When
        update_offer_and_stock_id_at_providers(venue_id=venue.id, old_siret=old_siret, lazy_run=False)

        # Then
        assert offer.isActive is False
        assert new_offer.isActive is True
        assert stock.isSoftDeleted is True
        assert new_stock.isSoftDeleted is False
        assert mock_repository.save.call_count == 3
        assert mock_repository.save.call_args_list == [call(offer), call(stock), call()]

    @patch("pcapi.scripts.stock.update_offer_and_stock_id_at_providers.repository")
    @pytest.mark.usefixtures("db_session")
    def should_keep_bookings_to_existing_stock(self, mock_repository, app):
        # Given
        old_siret = "85234081900014"
        current_siret = "32363560700019"
        venue = VenueFactory(siret=current_siret, id=12)
        offer = OfferFactory(venue=venue, idAtProviders=f"9782742785988@{old_siret}")
        stock = StockFactory(id=11, offer=offer, idAtProviders=f"9782742785988@{old_siret}")
        booking = BookingFactory(stock=stock)

        repository.save(booking)

        # When
        update_offer_and_stock_id_at_providers(venue_id=12, old_siret=old_siret, lazy_run=False)

        # Then
        assert booking.stockId == 11
        assert mock_repository.save.call_count == 3
        assert mock_repository.save.call_args_list == [call(offer), call(stock), call()]

    @patch("pcapi.scripts.stock.update_offer_and_stock_id_at_providers.repository")
    @pytest.mark.usefixtures("db_session")
    def should_switch_bookings_to_new_stock(self, mock_repository, app):
        # Given
        old_siret = "85234081900014"
        current_siret = "32363560700019"
        venue = VenueFactory(siret=current_siret, id=12)

        old_offer = OfferFactory(venue=venue, idAtProviders=f"9782742785988@{old_siret}")
        old_stock = StockFactory(id=100, offer=old_offer, idAtProviders=f"9782742785988@{old_siret}")
        booking = BookingFactory(stock=old_stock)

        valid_offer = OfferFactory(venue=venue, idAtProviders=f"9782742785988@{current_siret}")
        valid_stock = StockFactory(id=200, offer=valid_offer, idAtProviders=f"9782742785988@{current_siret}")

        repository.save(old_stock, valid_stock, booking)

        # When
        update_offer_and_stock_id_at_providers(venue_id=venue.id, old_siret=old_siret, lazy_run=False)

        # Then
        assert booking.stockId == valid_stock.id
        assert mock_repository.save.call_count == 3
        assert mock_repository.save.call_args_list == [call(old_offer), call(old_stock), call(booking)]

    @patch("pcapi.scripts.stock.update_offer_and_stock_id_at_providers.repository")
    @pytest.mark.usefixtures("db_session")
    def should_not_save_offer_with_bookings_errors(self, mock_repository, app):
        # Given
        old_siret = "85234081900014"
        current_siret = "32363560700019"
        venue = VenueFactory(siret=current_siret, id=12)

        valid_offer_product_ids = "9782742785988"
        not_valid_offer_product_ids = "1234567890987"
        old_offers = {}
        bookings = {}
        stocks = {}
        old_stocks = {}
        for product_id in [valid_offer_product_ids, not_valid_offer_product_ids]:

            stock_quantity = 1 if product_id == valid_offer_product_ids else 0
            offer = OfferFactory(venue=venue, idAtProviders=f"{product_id}@{current_siret}")
            stocks[product_id] = StockFactory(
                offer=offer, quantity=stock_quantity, idAtProviders=f"{product_id}@{current_siret}"
            )

            old_offers[product_id] = OfferFactory(venue=venue, idAtProviders=f"{product_id}@{old_siret}")
            old_stocks[product_id] = StockFactory(
                offer=old_offers[product_id], idAtProviders=f"{product_id}@{old_siret}"
            )
            bookings[product_id] = BookingFactory(stock=old_stocks[product_id])

            repository.save(old_stocks[product_id], stocks[product_id], bookings[product_id])

        # When
        update_offer_and_stock_id_at_providers(venue_id=venue.id, old_siret=old_siret, lazy_run=False)

        # Then
        assert bookings[valid_offer_product_ids].stockId == stocks[valid_offer_product_ids].id
        assert bookings[not_valid_offer_product_ids].stockId == old_stocks[not_valid_offer_product_ids].id
        assert mock_repository.save.call_count == 3
        assert mock_repository.save.call_args_list == [
            call(old_offers[valid_offer_product_ids]),
            call(old_stocks[valid_offer_product_ids]),
            call(bookings[valid_offer_product_ids]),
        ]

    class GetTiteliveOffersWithSiretInIdAtProvidersTest:
        @pytest.mark.usefixtures("db_session")
        def should_return_offers_with_siret_in_id_at_providers(self, app):
            # Given
            siret = "32363560700019"
            old_siret = "85234081900014"
            other_siret = "7863560700657"

            current_siret = "32363560700019"

            expected_venue = VenueFactory(siret=siret)
            other_venue = VenueFactory(siret=other_siret)
            offer = OfferFactory(venue=expected_venue, idAtProviders=f"9782742785988@{expected_venue.siret}")
            offer_with_old_siret = OfferFactory(venue=expected_venue, idAtProviders=f"9782742785988@{old_siret}")
            other_offer = OfferFactory(venue=other_venue, idAtProviders=f"9782742785988@{other_venue.siret}")

            repository.save(offer, offer_with_old_siret, other_offer)

            # When
            offers_result = _get_titelive_offers_with_siret_in_id_at_providers(expected_venue, current_siret)

            # Then
            assert offers_result == [offer]

    class CorrectIdAtProvidersTest:
        def should_replace_siret_in_id_at_providers_with_given_value(self):
            # Given
            old_siret = "85234081900014"
            current_siret = "32363560700019"
            current_id_at_providers = f"9782742785988@{old_siret}"

            # When
            result = _update_id_at_provider_siret(current_id_at_providers, current_siret)

            # Then
            assert result == f"9782742785988@{current_siret}"
