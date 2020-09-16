from datetime import datetime, timedelta

import pytest

from core.offers import api
from core.offers import factories
from core.offers import exceptions


class TestCancellation:

    def test_cancel(self):
        booking = factories.BookingFactory()
        api.cancel_booking(booking.user, booking)
        assert booking.isCancelled

    def test_raise_booking_is_already_used(self):
        booking = factories.BookingFactory(isUsed=True)

        with pytest.raises(exceptions.BookingIsAlreadyUsed):
            api.cancel_booking(booking.user, booking)
        assert not booking.isCancelled

    def test_raise_too_late_to_cancel(self):
        booking = factories.BookingFactory(
            product__offer__beginningDatetime=datetime.now() + timedelta(days=1),
        )
        with pytest.raises(exceptions.EventHappensInLessThan72Hours):
            api.cancel_booking(booking.user, booking)
        assert not booking.isCancelled
