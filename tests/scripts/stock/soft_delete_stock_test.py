import pytest

import pcapi.core.bookings.factories as bookings_factories
import pcapi.core.offers.factories as offer_factories
import pcapi.core.payments.factories as payment_factories
from pcapi.scripts.stock.soft_delete_stock import soft_delete_stock


class SoftDeleteStockTest:
    @pytest.mark.usefixtures("db_session")
    def should_return_ko_if_at_least_one_booking_is_used(self, app):
        # Given
        booking = bookings_factories.BookingFactory(isUsed=True)

        # When
        soft_delete_stock(booking.stock.id)

        # Then
        assert not booking.stock.isSoftDeleted

    @pytest.mark.usefixtures("db_session")
    def should_return_ko_if_at_least_one_booking_has_payments(self, app):
        # Given
        booking = bookings_factories.BookingFactory(isUsed=True)
        payment = payment_factories.PaymentFactory(booking=booking)

        # When
        soft_delete_stock(payment.booking.stock.id)

        # Then
        assert not booking.stock.isSoftDeleted

    @pytest.mark.usefixtures("db_session")
    def should_return_ok_if_stock_has_no_bookings_and_soft_delete_it(self, app):
        # Given
        stock = offer_factories.StockFactory()

        # When
        soft_delete_stock(stock.id)

        # Then
        assert stock.isSoftDeleted

    @pytest.mark.usefixtures("db_session")
    def should_cancel_every_bookings_for_target_stock(self, app):
        # Given
        booking = bookings_factories.BookingFactory()

        # When
        soft_delete_stock(booking.stock.id)

        # Then
        assert booking.isCancelled
