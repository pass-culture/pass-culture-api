from datetime import datetime, timedelta

import pytest

from models import Offer, Thing, Event, PcObject, ApiErrors, ThingType
from tests.conftest import clean_database
from tests.test_utils import create_thing, create_thing_offer, create_offerer, create_venue, \
    create_stock, create_booking, create_user
from utils.date import DateTimes

now = datetime.utcnow()
two_days_ago = now - timedelta(days=2)
four_days_ago = now - timedelta(days=4)
five_days_from_now = now + timedelta(days=5)
ten_days_from_now = now + timedelta(days=10)


class DateRangeTest:
    def test_is_empty_if_offer_is_on_a_thing(self):
        # given
        offer = Offer()
        offer.thing = Thing()
        offer.stocks = []

        # then
        assert offer.dateRange == DateTimes()

    def test_matches_the_occurrence_if_only_one_occurrence(self):
        # given
        offer = Offer()
        offer.event = Event()
        offer.stocks = [
            create_stock(offer, beginning_datetime=two_days_ago, end_datetime=five_days_from_now)
        ]

        # then
        assert offer.dateRange == DateTimes(two_days_ago, five_days_from_now)

    def test_starts_at_first_beginning_date_time_and_ends_at_last_end_date_time(self):
        # given
        offer = Offer()
        offer.event = Event()
        offer.stocks = [
            create_stock(offer, beginning_datetime=two_days_ago, end_datetime=five_days_from_now),
            create_stock(offer, beginning_datetime=four_days_ago, end_datetime=five_days_from_now),
            create_stock(offer, beginning_datetime=four_days_ago, end_datetime=ten_days_from_now),
            create_stock(offer, beginning_datetime=two_days_ago, end_datetime=ten_days_from_now)
        ]

        # then
        assert offer.dateRange == DateTimes(four_days_ago, ten_days_from_now)
        assert offer.dateRange.datetimes == [four_days_ago, ten_days_from_now]

    def test_is_empty_if_event_has_no_event_occurrences(self):
        # given
        offer = Offer()
        offer.event = Event()
        offer.stocks = []

        # then
        assert offer.dateRange == DateTimes()


@pytest.mark.standalone
class IsFullyBookedTest:
    def test_returns_true_if_all_available_stocks_are_booked(self):
        # given
        offer = Offer()
        user = create_user()
        stock1 = create_stock(available=2)
        stock2 = create_stock(available=1)
        stock3 = create_stock(available=1)
        create_booking(user, stock=stock1, quantity=2)
        create_booking(user, stock=stock2, quantity=1)
        create_booking(user, stock=stock3, quantity=1)
        offer.stocks = [stock1, stock2, stock3]

        # then
        assert offer.isFullyBooked is True

    def test_cancelled_bookings_are_ignored(self):
        # given
        offer = Offer()
        user = create_user()
        stock1 = create_stock(available=2)
        stock2 = create_stock(available=1)
        stock3 = create_stock(available=1)
        create_booking(user, stock=stock1, quantity=2, is_cancelled=True)
        create_booking(user, stock=stock2, quantity=1)
        create_booking(user, stock=stock3, quantity=1)
        offer.stocks = [stock1, stock2, stock3]

        # then
        assert offer.isFullyBooked is False

    def test_stocks_with_past_booking_limit_datetimes_are_ignored(self):
        # given
        offer = Offer()
        user = create_user()
        stock1 = create_stock(available=2, booking_limit_datetime=datetime.utcnow() - timedelta(weeks=3))
        stock2 = create_stock(available=1)
        stock3 = create_stock(available=1)
        create_booking(user, stock=stock2, quantity=1)
        create_booking(user, stock=stock3, quantity=1)
        offer.stocks = [stock1, stock2, stock3]

        # then
        assert offer.isFullyBooked is True


@clean_database
@pytest.mark.standalone
def test_create_digital_offer_success(app):
    # Given
    url = 'http://mygame.fr/offre'
    digital_thing = create_thing(thing_type=ThingType.JEUX_VIDEO, url=url, is_national=True)
    offerer = create_offerer()
    virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
    PcObject.check_and_save(virtual_venue)

    offer = create_thing_offer(virtual_venue, digital_thing)

    # When
    PcObject.check_and_save(digital_thing, offer)

    # Then
    assert offer.thing.url == url


@clean_database
@pytest.mark.standalone
def test_offer_error_when_thing_is_digital_but_venue_not_virtual(app):
    # Given
    digital_thing = create_thing(thing_type=ThingType.JEUX_VIDEO, url='http://mygame.fr/offre')
    offerer = create_offerer()
    physical_venue = create_venue(offerer)
    PcObject.check_and_save(physical_venue)
    offer = create_thing_offer(physical_venue, digital_thing)

    # When
    with pytest.raises(ApiErrors) as errors:
        PcObject.check_and_save(offer)

    # Then
    assert errors.value.errors['venue'] == [
        'Une offre numérique doit obligatoirement être associée au lieu "Offre en ligne"']


@pytest.mark.standalone
def test_offer_as_dict_returns_dateRange_in_ISO_8601(app):
    # Given
    offer = Offer()
    offer.stocks = [
        create_stock(offer=offer,
                     beginning_datetime=datetime(2018, 10, 22, 10, 10, 10),
                     end_datetime=datetime(2018, 10, 22, 13, 10, 10))
    ]

    # When
    offer_dict = offer._asdict(include=["dateRange"])

    # Then
    assert offer_dict['dateRange'] == ['2018-10-22T10:10:10Z', '2018-10-22T13:10:10Z']
