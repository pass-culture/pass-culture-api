from datetime import datetime

from domain.bookings import generate_bookings_details_csv
from models import Booking, PcObject
from tests.conftest import clean_database
from tests.test_utils import create_booking, create_deposit, create_stock, create_user, create_offerer, create_venue, \
    create_offer_with_thing_product


class BookingsCSVTest:
    def test_generate_bookings_details_csv_with_headers_and_zero_bookings_lines(self):
        # given
        bookings = []

        # when
        csv = generate_bookings_details_csv(bookings)

        # then
        assert _count_non_empty_lines(csv) == 1

    def test_generate_bookings_details_csv_has_human_readable_header(self):
        # given
        bookings = []

        # when
        csv = generate_bookings_details_csv(bookings)

        # then
        assert _get_header(
            csv) == 'Raison sociale du lieu;Nom de l\'offre;Nom utilisateur;Prénom utilisateur;E-mail utilisateur;Date de la réservation;Quantité;Tarif pass Culture;Statut'

    @clean_database
    def test_generate_bookings_details_csv_with_headers_and_three_bookings_lines(self, app):
        # given
        user = create_user(email='jane.doe@test.com', idx=3)
        offerer = create_offerer(siren='987654321', name='Joe le Libraire')
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(price=12, available=5, offer=offer)
        booking = create_booking(user, stock, date_created=datetime(2010, 1, 1, 0, 0, 0, 0))
        deposit1 = create_deposit(user, amount=100)

        PcObject.save(user, offerer, venue, offer, stock, booking, deposit1)

        bookings = Booking.query.all()

        expected_line = 'La petite librairie;Test Book;Doe;John;jane.doe@test.com;2010-01-01 00:00:00;1;12;En attente'

        # when
        csv = generate_bookings_details_csv(bookings)

        # then
        assert _count_non_empty_lines(csv) == 2
        assert csv.split('\r\n')[1] == expected_line


def _get_header(csv):
    return csv.split('\r\n')[0]


def _count_non_empty_lines(csv):
    return len(list(filter(lambda line: line != '', csv.split('\r\n'))))
