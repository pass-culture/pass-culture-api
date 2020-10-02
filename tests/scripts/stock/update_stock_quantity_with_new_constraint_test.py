from datetime import datetime, timedelta
from unittest.mock import patch, call, MagicMock

from models import StockSQLEntity
from models.db import db
from repository import repository
from scripts.stock.update_stock_quantity_with_new_constraint import (
    update_stock_quantity_with_new_constraint,
    _get_old_remaining_quantity,
    _get_stocks_to_check,
    _get_stocks_with_negative_remaining_quantity,
    update_stock_quantity_for_negative_remaining_quantity,
)
from tests.conftest import clean_database
from tests.model_creators.generic_creators import (
    create_offerer,
    create_venue,
    create_stock,
    create_booking,
    create_user,
)
from tests.model_creators.specific_creators import create_offer_with_thing_product


class GetOldRemainingQuantityTest:
    @clean_database
    def test_should_return_old_remaining_quantity(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(
            date_modified=datetime.utcnow(), offer=offer, price=0, quantity=12
        )
        yesterday = datetime.utcnow() - timedelta(days=1)
        booking_used_before_stock_update = create_booking(
            user, stock=stock, quantity=2, is_used=True, date_used=yesterday
        )
        booking_cancelled = create_booking(
            user, stock=stock, quantity=2, is_cancelled=True
        )
        repository.save(booking_used_before_stock_update, booking_cancelled)

        # When
        result = _get_old_remaining_quantity(stock)

        # Then
        assert result == 12


class GetStocksToCheckTest:
    @clean_database
    def test_should_not_return_stocks_with_no_bookings(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, quantity=12)
        repository.save(stock)

        # When
        stocks = _get_stocks_to_check()

        # Then
        assert stocks == []

    @clean_database
    def test_should_not_return_soft_deleted_stocks(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(is_soft_deleted=True, offer=offer, price=0, quantity=12)
        booking = create_booking(user, stock=stock)
        repository.save(booking)

        # When
        stocks = _get_stocks_to_check()

        # Then
        assert stocks == []

    @clean_database
    def test_should_not_return_stock_with_unlimited_quantity(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0, quantity=None)
        booking = create_booking(user, stock=stock)
        repository.save(booking)

        # When
        stocks = _get_stocks_to_check()

        # Then
        assert stocks == []

    @clean_database
    def test_should_not_return_stock_that_has_already_been_migrated(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(has_been_migrated=True, offer=offer, price=0, quantity=10)
        booking = create_booking(user, stock=stock)
        repository.save(booking)

        # When
        stocks = _get_stocks_to_check()

        # Then
        assert stocks == []
