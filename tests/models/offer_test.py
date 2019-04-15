from datetime import datetime, timedelta

import pytest

from models import Offer, Thing, Event, PcObject, ApiErrors, ThingType, EventType
from tests.conftest import clean_database
from tests.test_utils import create_thing, create_thing_offer, create_offerer, create_venue, \
    create_stock, create_booking, create_user, create_event_occurrence
from tests.test_utils import create_event_offer
from utils.date import DateTimes

now = datetime.utcnow()
two_days_ago = now - timedelta(days=2)
four_days_ago = now - timedelta(days=4)
five_days_from_now = now + timedelta(days=5)
ten_days_from_now = now + timedelta(days=10)


@pytest.mark.standalone
class DateRangeTest:
    def test_offer_as_dict_returns_dateRange_in_ISO_8601(self):
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
class CreateOfferTest:
    @clean_database
    def test_success_when_is_digital_and_virtual_venue(self, app):
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
        assert offer.url == url

    @clean_database
    def test_success_when_is_physical_and_physical_venue(self, app):
        # Given
        physical_thing = create_thing(thing_type=ThingType.LIVRE_EDITION, url=None)
        offerer = create_offerer()
        physical_venue = create_venue(offerer, is_virtual=False, siret=offerer.siren + '12345')
        PcObject.check_and_save(physical_venue)
        offer = create_thing_offer(physical_venue, physical_thing)

        # When
        PcObject.check_and_save(physical_thing, offer)

        # Then
        assert offer.url is None

    @clean_database
    def test_fails_when_is_digital_but_physical_venue(self, app):
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

    @clean_database
    def test_fails_when_is_physical_but_venue_is_virtual(self, app):
        # Given
        physical_thing = create_thing(thing_type=ThingType.JEUX_VIDEO, url=None)
        offerer = create_offerer()
        digital_venue = create_venue(offerer, is_virtual=True, siret=None)
        PcObject.check_and_save(digital_venue)
        offer = create_thing_offer(digital_venue, physical_thing)

        # When
        with pytest.raises(ApiErrors) as errors:
            PcObject.check_and_save(offer)

        # Then
        assert errors.value.errors['venue'] == [
            'Une offre physique ne peut être associée au lieu "Offre en ligne"']

    @clean_database
    def test_create_digital_offer_success(self, app):
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
    def test_offer_error_when_thing_is_digital_but_venue_not_virtual(self, app):
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


def test_offer_is_digital_if_it_has_an_url():
    # given
    offer = Offer()
    offer.url = 'http://url.com'

    # when / then
    assert offer.isDigital


def test_thing_offer_offerType_returns_dict_matching_ThingType_enum():
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_thing_offer(venue, thing_type=ThingType.LIVRE_EDITION)
    expected_value = {
        'conditionalFields': ["author", "isbn"],
        'label': 'Livre — Édition',
        'offlineOnly': False,
        'onlineOnly': False,
        'sublabel': 'Lire',
        'description': 'S’abonner à un quotidien d’actualité ?'
                       ' À un hebdomadaire humoristique ? '
                       'À un mensuel dédié à la nature ? '
                       'Acheter une BD ou un manga ? '
                       'Ou tout simplement ce livre dont tout le monde parle ?',
        'value': 'ThingType.LIVRE_EDITION',
        'type': 'Thing'
    }

    # when
    offer_type = offer.offerType

    # then
    assert offer_type == expected_value


def test_event_offer_offerType_returns_dict_matching_EventType_enum():
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue, event_type=EventType.SPECTACLE_VIVANT)
    expected_value = {
        'conditionalFields': ["author", "showType", "stageDirector", "performer"],
        'label': "Spectacle vivant",
        'offlineOnly': True,
        'onlineOnly': False,
        'sublabel': "Applaudir",
        'description': "Suivre un géant de 12 mètres dans la ville ? "
                       "Rire aux éclats devant un stand up ?"
                       " Rêver le temps d’un opéra ou d’un spectacle de danse ? "
                       "Assister à une pièce de théâtre, ou se laisser conter une histoire ?",
        'value': 'EventType.SPECTACLE_VIVANT',
        'type': 'Event'
    }

    # when
    offer_type = offer.offerType

    # then
    assert offer_type == expected_value


def test_thing_offer_offerType_returns_None_if_type_does_not_match_ThingType_enum():
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_thing_offer(venue, thing_type='')

    # when
    offer_type = offer.offerType

    # then
    assert offer_type == None


def test_event_offer_offerType_returns_None_if_type_does_not_match_EventType_enum():
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue, event_type='Workshop')

    # when
    offer_type = offer.offerType

    # then
    assert offer_type == None


@pytest.mark.standalone
class IsFullyBookedTest:
    class WhenOfferOnThingTest:
        def test_returns_true_if_all_available_stocks_are_booked(self):
            # given
            offer = Offer()
            offer.thing = Thing()
            user = create_user()
            stock1 = create_stock(available=2)
            stock2 = create_stock(available=1)
            create_booking(user, stock=stock1, quantity=1)
            create_booking(user, stock=stock1, quantity=1)
            create_booking(user, stock=stock2, quantity=1)
            offer.thingStocks = [stock1, stock2]

            # then
            assert offer.isFullyBooked is True

        def test_cancelled_bookings_are_ignored(self):
            # given
            offer = Offer()
            offer.thing = Thing()
            user = create_user()
            stock1 = create_stock(available=2)
            stock2 = create_stock(available=1)
            create_booking(user, stock=stock1, quantity=1)
            create_booking(user, stock=stock1, quantity=1, is_cancelled=True)
            create_booking(user, stock=stock2, quantity=1)
            offer.thingStocks = [stock1, stock2]

            # then
            assert offer.isFullyBooked is False

    class WhenOfferOnEventTest:
        def test_returns_true_if_all_available_stocks_are_booked(self):
            # given
            offer = Offer()
            offer.event = Event()
            user = create_user()
            stock1 = create_stock(available=2)
            stock2 = create_stock(available=1)
            stock3 = create_stock(available=1)
            occurrence1 = create_event_occurrence(offer)
            occurrence2 = create_event_occurrence(offer)
            occurrence1.stocks = [stock1, stock2]
            occurrence2.stocks = [stock3]
            create_booking(user, stock=stock1, quantity=2)
            create_booking(user, stock=stock2, quantity=1)
            create_booking(user, stock=stock3, quantity=1)
            offer.eventOccurrences = [occurrence1, occurrence2]

            # then
            assert offer.isFullyBooked is True

        def test_cancelled_bookings_are_ignored(self):
            # given
            offer = Offer()
            offer.event = Event()
            user = create_user()
            stock1 = create_stock(available=2)
            stock2 = create_stock(available=1)
            stock3 = create_stock(available=1)
            occurrence1 = create_event_occurrence(offer)
            occurrence2 = create_event_occurrence(offer)
            occurrence1.stocks = [stock1, stock2]
            occurrence2.stocks = [stock3]
            create_booking(user, stock=stock1, quantity=2, is_cancelled=True)
            create_booking(user, stock=stock2, quantity=1)
            create_booking(user, stock=stock3, quantity=1)
            offer.eventOccurrences = [occurrence1, occurrence2]

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
