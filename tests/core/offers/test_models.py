from core.offers.models import Booking


class TestBooking:
    def test_total_amount(self):
        booking = Booking(amount=1.2, quantity=2)
        assert booking.total_amount == 2.4
