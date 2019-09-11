from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from models import Offer, PcObject, Stock, Product, Criterion, OfferCriterion
from models.offer_type import EventType, ThingType
from repository.offer_queries import department_or_national_offers, \
    find_activation_offers, \
    find_offers_with_filter_parameters, \
    get_offers_for_recommendations_search, \
    get_active_offers, \
    _build_has_remaining_stock_predicate,\
    find_offers_by_venue_id, \
    order_by_with_criteria
from tests.conftest import clean_database
from tests.test_utils import create_booking, \
    create_criterion, \
    create_product_with_event_type, \
    create_event_occurrence, \
    create_offer_with_event_product, \
    create_mediation, \
    create_stock_from_event_occurrence, \
    create_product_with_thing_type, \
    create_offer_with_thing_product, \
    create_offerer, \
    create_stock_from_offer, \
    create_stock_with_event_offer, \
    create_stock_with_thing_offer, \
    create_user_offerer, \
    create_user, \
    create_venue

REFERENCE_DATE = '2017-10-15 09:21:34'


class DepartmentOrNationalOffersTest:
    @clean_database
    def test_returns_national_thing_with_different_department(self, app):
        # given
        product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')
        offer = create_offer_with_thing_product(venue, product)
        PcObject.save(offer)
        query = Product.query.filter_by(name='Lire un livre')

        # when
        query = department_or_national_offers(query, ['93'])

        # then
        assert product in query.all()

    @clean_database
    def test_returns_national_event_with_different_department(self, app):
        # given
        product = create_product_with_event_type('Voir une pièce', is_national=True)
        offerer = create_offerer()
        venue = create_venue(offerer, is_virtual=False, postal_code='29000', departement_code='29')
        offer = create_offer_with_event_product(venue, product)
        PcObject.save(offer)
        query = Product.query.filter_by(name='Voir une pièce')

        # when
        query = department_or_national_offers(query, ['93'])

        # then
        assert product in query.all()

    @clean_database
    def test_returns_nothing_if_event_is_not_in_given_department_list(self, app):
        # given
        product = create_product_with_event_type('Voir une pièce', is_national=False)
        offerer = create_offerer()
        venue = create_venue(offerer, is_virtual=False, postal_code='29000', departement_code='29')
        offer = create_offer_with_event_product(venue, product)
        PcObject.save(offer)
        query = Product.query.filter_by(name='Voir une pièce')

        # when
        query = department_or_national_offers(query, ['34'])

        # then
        assert query.count() == 0

    @clean_database
    def test_returns_an_event_regardless_of_department_if_department_list_contains_00(self, app):
        # given
        product = create_product_with_event_type('Voir une pièce', is_national=False)
        offerer = create_offerer()
        venue = create_venue(offerer, is_virtual=False, postal_code='29000', departement_code='29')
        offer = create_offer_with_event_product(venue, product)
        PcObject.save(offer)
        query = Product.query.filter_by(name='Voir une pièce')

        # when
        query = department_or_national_offers(query, ['00'])

        # then
        assert query.count() == 1

    @clean_database
    def test_returns_an_event_if_it_is_given_in_department_list(self, app):
        # given
        product = create_product_with_event_type('Voir une pièce', is_national=False)
        offerer = create_offerer()
        venue = create_venue(offerer, is_virtual=False, postal_code='29000', departement_code='29')
        offer = create_offer_with_event_product(venue, product)
        PcObject.save(offer)
        query = Product.query.filter_by(name='Voir une pièce')

        # when
        query = department_or_national_offers(query, ['29'])

        # then
        assert query.count() == 1


@freeze_time(REFERENCE_DATE)
class GetOffersForRecommendationsSearchTest:
    @clean_database
    def test_search_by_one_event_type_returns_only_offers_on_events_of_that_type(self, app):
        # Given
        type_label = EventType.CONFERENCE_DEBAT_DEDICACE
        other_type_label = EventType.MUSIQUE

        conference_event1 = create_product_with_event_type('Rencontre avec Franck Lepage', event_type=type_label)
        conference_event2 = create_product_with_event_type('Conférence ouverte', event_type=type_label)
        concert_event = create_product_with_event_type('Concert de Gael Faye', event_type=other_type_label)

        offerer = create_offerer(
            siren='507633576',
            address='1 BD POISSONNIERE',
            city='Paris',
            postal_code='75002',
            name='LE GRAND REX PARIS',
            validation_token=None,
        )
        venue = create_venue(
            offerer,
            name='LE GRAND REX PARIS',
            address="1 BD POISSONNIERE",
            postal_code='75002',
            city="Paris",
            departement_code='75',
            is_virtual=False,
            longitude="2.4002701",
            latitude="48.8363788",
            siret="50763357600016"
        )

        conference_offer1 = create_offer_with_event_product(venue, conference_event1)
        conference_offer2 = create_offer_with_event_product(venue, conference_event2)
        concert_offer = create_offer_with_event_product(venue, concert_event)

        conference_event_occurrence1 = create_event_occurrence(conference_offer1)
        conference_event_occurrence2 = create_event_occurrence(conference_offer2)
        concert_event_occurrence = create_event_occurrence(concert_offer)

        conference_stock1 = create_stock_from_event_occurrence(conference_event_occurrence1)
        conference_stock2 = create_stock_from_event_occurrence(conference_event_occurrence2)
        concert_stock = create_stock_from_event_occurrence(concert_event_occurrence)

        PcObject.save(conference_stock1, conference_stock2, concert_stock)

        # When
        offers = get_offers_for_recommendations_search(
            type_values=[
                str(type_label)
            ],
        )

        # Then
        assert conference_offer1 in offers
        assert conference_offer2 in offers
        assert concert_offer not in offers

    @clean_database
    def test_search_by_one_thing_type_returns_only_offers_on_things_of_that_type(self, app):
        # Given
        type_label_ok = ThingType.JEUX_VIDEO
        type_label_ko = ThingType.LIVRE_EDITION

        thing_ok1 = create_product_with_thing_type(thing_type=type_label_ok)
        thing_ok2 = create_product_with_thing_type(thing_type=type_label_ok)
        thing_ko = create_product_with_thing_type(thing_type=type_label_ko)
        event_ko = create_product_with_event_type(event_type=EventType.CINEMA)

        offerer = create_offerer()
        venue = create_venue(offerer)

        ok_offer_1 = create_offer_with_thing_product(venue, thing_ok1)
        ok_offer_2 = create_offer_with_thing_product(venue, thing_ok2)
        ko_offer = create_offer_with_thing_product(venue, thing_ko)
        ko_event_offer = create_offer_with_event_product(venue, event_ko)

        ko_event_occurrence = create_event_occurrence(ko_event_offer)

        ok_stock1 = create_stock_from_offer(ok_offer_1)
        ok_stock2 = create_stock_from_offer(ok_offer_2)
        ko_stock1 = create_stock_from_offer(ko_offer)
        ko_stock2 = create_stock_from_event_occurrence(ko_event_occurrence)

        PcObject.save(ok_stock1, ok_stock2, ko_stock1, ko_stock2)

        # When
        offers = get_offers_for_recommendations_search(
            type_values=[
                str(type_label_ok)
            ],
        )

        # Then
        assert len(offers) == 2
        assert ok_offer_1 in offers
        assert ok_offer_2 in offers

    @clean_database
    def test_search_by_datetime_only_returns_recommendations_starting_during_time_interval(self, app):
        # Duplicate
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)

        ok_stock = _create_event_stock_and_offer_for_date(venue, datetime(2018, 1, 6, 12, 30))
        ko_stock_before = _create_event_stock_and_offer_for_date(venue, datetime(2018, 1, 1, 12, 30))
        ko_stock_after = _create_event_stock_and_offer_for_date(venue, datetime(2018, 1, 10, 12, 30))
        ok_stock_with_thing = create_stock_with_thing_offer(offerer, venue)

        PcObject.save(ok_stock, ko_stock_before, ko_stock_after)

        # When
        search_result_offers = get_offers_for_recommendations_search(
            days_intervals=[
                [datetime(2018, 1, 6, 12, 0), datetime(2018, 1, 6, 13, 0)]
            ],
        )

        # Then
        assert ok_stock.resolvedOffer in search_result_offers
        assert ok_stock_with_thing.resolvedOffer in search_result_offers
        assert ko_stock_before.resolvedOffer not in search_result_offers
        assert ko_stock_after.resolvedOffer not in search_result_offers

    @clean_database
    def test_search_with_several_partial_keywords_returns_things_and_events_with_name_containing_keywords(self, app):
        # Given
        thing_ok = create_product_with_thing_type(thing_name='Rencontre de michel')
        thing_product = create_product_with_thing_type(thing_name='Rencontre avec jean-luc')
        event_product = create_product_with_event_type(event_name='Rencontre avec jean-mimi chelou')
        offerer = create_offerer()
        venue = create_venue(offerer)
        thing_ok_offer = create_offer_with_thing_product(venue, thing_ok)
        thing_ko_offer = create_offer_with_thing_product(venue, thing_product)
        event_ko_offer = create_offer_with_event_product(venue, event_product)
        event_ko_occurrence = create_event_occurrence(event_ko_offer)
        event_ko_stock = create_stock_from_event_occurrence(event_ko_occurrence)
        thing_ok_stock = create_stock_from_offer(thing_ok_offer)
        thing_ko_stock = create_stock_from_offer(thing_ko_offer)
        PcObject.save(event_ko_stock, thing_ok_stock, thing_ko_stock)

        # When
        offers = get_offers_for_recommendations_search(keywords_string='renc michel')

        # Then
        assert thing_ok_offer in offers
        assert thing_ko_offer not in offers
        assert event_ko_offer not in offers

    @clean_database
    def test_search_without_accents_matches_offer_with_accents_1(self, app):
        # Given
        thing_product_ok = create_product_with_thing_type(thing_name='Nez à nez')
        offerer = create_offerer()
        venue = create_venue(offerer)
        thing_ok_offer = create_offer_with_thing_product(venue, thing_product_ok)
        thing_ok_stock = create_stock_from_offer(thing_ok_offer)
        PcObject.save(thing_ok_stock)

        # When
        offers = get_offers_for_recommendations_search(keywords_string='nez a')

        # Then
        assert thing_ok_offer in offers

    @clean_database
    def test_search_with_accents_matches_offer_without_accents_2(self, app):
        # Given
        thing_ok = create_product_with_thing_type(thing_name='Déjà')
        offerer = create_offerer()
        venue = create_venue(offerer)
        thing_ok_offer = create_offer_with_thing_product(venue, thing_ok)
        thing_ok_stock = create_stock_from_offer(thing_ok_offer)
        PcObject.save(thing_ok_stock)

        # When
        offers = get_offers_for_recommendations_search(keywords_string='deja')

        #
        assert thing_ok_offer in offers

    @clean_database
    def test_search_does_not_return_offers_by_types_with_booking_limit_date_over(self, app):
        # Given
        three_hours_ago = datetime.utcnow() - timedelta(hours=3)
        type_label = ThingType.JEUX_VIDEO
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, thing_type=type_label)
        outdated_stock = create_stock_from_offer(offer, booking_limit_datetime=three_hours_ago)

        PcObject.save(outdated_stock)

        # When
        search_result_offers = get_offers_for_recommendations_search(type_values=[
            str(type_label)
        ], )

        # Then
        assert not search_result_offers

    @clean_database
    def test_search_does_not_return_offers_by_types_with_all_beginning_datetime_passed_and_no_booking_limit_datetime(
            self, app):
        # Given
        three_hours_ago = datetime.utcnow() - timedelta(hours=3)
        type_label = EventType.MUSEES_PATRIMOINE
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, event_type=type_label)
        outdated_event_occurrence = create_event_occurrence(offer, beginning_datetime=three_hours_ago,
                                                            end_datetime=datetime.utcnow())
        stock = create_stock_from_event_occurrence(outdated_event_occurrence, booking_limit_date=None)

        PcObject.save(stock)

        # When
        search_result_offers = get_offers_for_recommendations_search(type_values=[
            str(type_label)
        ], )

        # Then
        assert not search_result_offers

    @clean_database
    def test_search_return_offers_by_types_with_some_but_not_all_beginning_datetime_passed_and_no_booking_limit_datetime(
            self, app):
        # Given
        three_hours_ago = datetime.utcnow() - timedelta(hours=3)
        in_three_hours = datetime.utcnow() + timedelta(hours=3)
        in_four_hours = datetime.utcnow() + timedelta(hours=4)
        type_label = EventType.MUSEES_PATRIMOINE
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, event_type=type_label)
        outdated_event_occurrence = create_event_occurrence(offer, beginning_datetime=three_hours_ago,
                                                            end_datetime=datetime.utcnow())
        future_event_occurrence = create_event_occurrence(offer, beginning_datetime=in_three_hours,
                                                          end_datetime=in_four_hours)
        future_stock = create_stock_from_event_occurrence(future_event_occurrence, booking_limit_date=None)
        outdated_stock = create_stock_from_event_occurrence(outdated_event_occurrence, booking_limit_date=None)

        PcObject.save(future_stock, outdated_stock)

        # When
        search_result_offers = get_offers_for_recommendations_search(type_values=[
            str(type_label)
        ], )

        # Then
        assert offer in search_result_offers


class GetActiveOffersTest:
    @clean_database
    def test_when_departement_code_00(app):
        # Given
        offerer = create_offerer()
        venue_34 = create_venue(offerer, postal_code='34000', departement_code='34', siret=offerer.siren + '11111')
        venue_93 = create_venue(offerer, postal_code='93000', departement_code='93', siret=offerer.siren + '22222')
        venue_75 = create_venue(offerer, postal_code='75000', departement_code='75', siret=offerer.siren + '33333')
        offer_34 = create_offer_with_thing_product(venue_34)
        offer_93 = create_offer_with_thing_product(venue_93)
        offer_75 = create_offer_with_thing_product(venue_75)
        stock_34 = create_stock_from_offer(offer_34)
        stock_93 = create_stock_from_offer(offer_93)
        stock_75 = create_stock_from_offer(offer_75)
        user = create_user(departement_code='00')

        PcObject.save(user, stock_34, stock_93, stock_75)

        # When
        offers = get_active_offers(departement_codes=['00'], offer_id=None)

        # Then
        assert offer_34 in offers
        assert offer_93 in offers
        assert offer_75 in offers

    @clean_database
    def test_only_returns_both_EventType_and_ThingType(app):
        # Given
        user = create_user(departement_code='93')
        offerer = create_offerer()
        venue = create_venue(offerer, departement_code='93')
        offer1 = create_offer_with_thing_product(venue, thumb_count=1)
        offer2 = create_offer_with_event_product(venue, thumb_count=1)
        now = datetime.utcnow()
        event_occurrence = create_event_occurrence(offer2, beginning_datetime=now + timedelta(hours=72),
                                                   end_datetime=now + timedelta(hours=74))
        mediation = create_mediation(offer2)
        stock1 = create_stock_from_offer(offer1, price=0)
        stock2 = create_stock_from_event_occurrence(event_occurrence, price=0, available=10,
                                                    booking_limit_date=now + timedelta(days=2))
        PcObject.save(user, stock1, stock2, mediation)

        # When
        offers = get_active_offers(user=user, departement_codes=['93'])
        # Then
        assert len(offers) == 2

    @clean_database
    def test_should_not_return_activation_event(app):
        # Given
        offerer = create_offerer()
        venue_93 = create_venue(offerer, postal_code='93000', departement_code='93', siret=offerer.siren + '33333')
        offer_93 = create_offer_with_event_product(venue_93, thumb_count=1)
        offer_activation_93 = create_offer_with_event_product(venue_93, event_type=EventType.ACTIVATION,
                                                              thumb_count=1)
        event_occurrence_93 = create_event_occurrence(offer_93)
        event_occurrence_activation_93 = create_event_occurrence(offer_activation_93)
        stock_93 = create_stock_from_event_occurrence(event_occurrence_93)
        stock_activation_93 = create_stock_from_event_occurrence(event_occurrence_activation_93)
        user = create_user(departement_code='00')

        PcObject.save(user, stock_93, stock_activation_93)

        # When
        offers = get_active_offers(user=user, departement_codes=['00'], offer_id=None)

        # Then
        assert offer_93 in offers
        assert offer_activation_93 not in offers

    @clean_database
    def test_should_not_return_activation_thing(app):
        # Given
        offerer = create_offerer()
        venue_93 = create_venue(offerer, postal_code='93000', departement_code='93', siret=offerer.siren + '33333')
        thing_93 = create_offer_with_thing_product(venue_93)
        thing_activation_93 = create_offer_with_thing_product(venue_93, thing_type=ThingType.ACTIVATION)
        stock_93 = create_stock_from_offer(thing_93)
        stock_activation_93 = create_stock_from_offer(thing_activation_93)
        user = create_user(departement_code='00')

        PcObject.save(user, stock_93, stock_activation_93)

        # When
        offers = get_active_offers(user=user, departement_codes=['00'], offer_id=None)

        # Then
        assert thing_93 in offers
        assert thing_activation_93 not in offers

    @clean_database
    def test_should_return_offers_with_stock(app):
        # Given
        product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')
        offer = create_offer_with_thing_product(venue, product)
        stock = create_stock_from_offer(offer, available=2)
        booking = create_booking(create_user(), stock, venue=venue, quantity=2, is_cancelled=True)
        PcObject.save(booking)

        # When
        offers = get_active_offers(user=create_user(email="plop@plop.com"), departement_codes=['00'], offer_id=None)

        # Then
        assert len(offers) == 1

    @clean_database
    @pytest.mark.standalone
    def test_should_return_offers_with_mediations_first(app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        stock1 = create_stock_with_thing_offer(offerer, venue, name='thing_with_mediation')
        mediation = create_mediation(stock1.offer)

        stock2 = create_stock_with_thing_offer(offerer, venue, name='thing_without_mediation')

        PcObject.save(stock2, mediation)
        PcObject.save(stock1)

        # When
        offers = get_active_offers(user=create_user(email="plop@plop.com"),
                                   departement_codes=['00'],
                                   offer_id=None)

        # Then
        assert len(offers) == 2
        assert offers[0].name == 'thing_with_mediation'
        assert offers[1].name == 'thing_without_mediation'

    @clean_database
    @pytest.mark.standalone
    def test_should_return_offers_that_occur_in_less_than_10_days_and_things_first(app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        stock1 = create_stock_with_thing_offer(offerer, venue, name='thing')
        stock2 = create_stock_with_event_offer(offerer,
                                               venue,
                                               beginning_datetime=datetime.utcnow() + timedelta(days=4),
                                               end_datetime=datetime.utcnow() + timedelta(days=4, hours=2),
                                               name='event_occurs_soon',
                                               thumb_count=1)
        stock3 = create_stock_with_event_offer(offerer,
                                               venue,
                                               beginning_datetime=datetime.utcnow() + timedelta(days=11),
                                               end_datetime=datetime.utcnow() + timedelta(days=11, hours=2),
                                               name='event_occurs_later',
                                               thumb_count=1)

        PcObject.save(stock3)
        PcObject.save(stock2)
        PcObject.save(stock1)

        # When
        offers = get_active_offers(user=create_user(email="plop@plop.com"),
                                   departement_codes=['00'],
                                   offer_id=None)

        # Then
        assert len(offers) == 3
        assert (offers[0].name == 'event_occurs_soon'
                and offers[1].name == 'thing') \
               or (offers[1].name == 'event_occurs_soon'
                   and offers[0].name == 'thing')
        assert offers[2].name == 'event_occurs_later'

    @clean_database
    @pytest.mark.standalone
    def test_should_return_offers_with_varying_types(app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        stock1 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock2 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO,
                                               url='http://example.com')
        stock3 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock4 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock5 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.AUDIOVISUEL)
        stock6 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX)

        PcObject.save(stock1, stock2, stock3, stock4, stock5, stock6)

        def first_four_offers_have_different_type_and_onlineness(offers):
            return len(set([o.type + (o.url or '')
                            for o in offers[:4]])) == 4

        # When
        offers = get_active_offers(user=create_user(email="plop@plop.com"),
                                   departement_codes=['00'],
                                   offer_id=None)

        # Then
        assert len(offers) == 6
        assert first_four_offers_have_different_type_and_onlineness(offers)

    @clean_database
    @pytest.mark.standalone
    def test_should_not_return_offers_with_no_stock(app):
        # Given
        product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')
        offer = create_offer_with_thing_product(venue, product)
        stock = create_stock_from_offer(offer, available=2, price=0)
        user = create_user()
        booking1 = create_booking(user, stock, venue=venue, quantity=2, is_cancelled=True)
        booking2 = create_booking(user, stock, venue=venue, quantity=2)
        PcObject.save(booking1, booking2)

        # When
        offers = get_active_offers(user=create_user(email="plop@plop.com"), departement_codes=['00'], offer_id=None)

        # Then
        assert len(offers) == 0


@clean_database
def test_find_activation_offers_returns_activation_offers_in_given_departement(app):
    # given
    offerer = create_offerer()
    venue1 = create_venue(offerer, siret=offerer.siren + '12345', postal_code='34000', departement_code='34')
    venue2 = create_venue(offerer, siret=offerer.siren + '54321', postal_code='93000', departement_code='93')
    offer1 = create_offer_with_event_product(venue1, event_type=EventType.ACTIVATION)
    offer2 = create_offer_with_event_product(venue1, event_type=EventType.SPECTACLE_VIVANT)
    offer3 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION)
    stock1 = create_stock_from_offer(offer1)
    stock2 = create_stock_from_offer(offer2)
    stock3 = create_stock_from_offer(offer3)
    PcObject.save(stock1, stock2, stock3)

    # when
    offers = find_activation_offers('34').all()

    # then
    assert len(offers) == 1


@clean_database
def test_find_activation_offers_returns_activation_offers_if_offer_is_national(app):
    # given
    offerer = create_offerer()
    venue1 = create_venue(offerer, siret=offerer.siren + '12345', postal_code='34000', departement_code='34')
    venue2 = create_venue(offerer, siret=offerer.siren + '54321', postal_code='93000', departement_code='93')
    offer1 = create_offer_with_event_product(venue1, event_type=EventType.ACTIVATION)
    offer2 = create_offer_with_thing_product(venue1, thing_type=ThingType.AUDIOVISUEL)
    offer3 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION, is_national=True)
    offer4 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION, is_national=True)
    stock1 = create_stock_from_offer(offer1)
    stock2 = create_stock_from_offer(offer2)
    stock3 = create_stock_from_offer(offer3)
    stock4 = create_stock_from_offer(offer4)
    PcObject.save(stock1, stock2, stock3, stock4)

    # when
    offers = find_activation_offers('34').all()

    # then
    assert len(offers) == 3


@clean_database
def test_find_activation_offers_returns_activation_offers_in_all_ile_de_france_if_departement_is_93(app):
    # given
    offerer = create_offerer()
    venue1 = create_venue(offerer, siret=offerer.siren + '12345', postal_code='34000', departement_code='34')
    venue2 = create_venue(offerer, siret=offerer.siren + '67890', postal_code='75000', departement_code='75')
    venue3 = create_venue(offerer, siret=offerer.siren + '54321', postal_code='78000', departement_code='78')
    offer1 = create_offer_with_event_product(venue1, event_type=EventType.ACTIVATION)
    offer2 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION)
    offer3 = create_offer_with_event_product(venue3, event_type=EventType.ACTIVATION)
    stock1 = create_stock_from_offer(offer1)
    stock2 = create_stock_from_offer(offer2)
    stock3 = create_stock_from_offer(offer3)
    PcObject.save(stock1, stock2, stock3)

    # when
    offers = find_activation_offers('93').all()

    # then
    assert len(offers) == 2


@clean_database
def test_find_activation_offers_returns_activation_offers_with_available_stocks(app):
    # given
    offerer = create_offerer()
    venue1 = create_venue(offerer, siret=offerer.siren + '12345', postal_code='93000', departement_code='93')
    venue2 = create_venue(offerer, siret=offerer.siren + '67890', postal_code='93000', departement_code='93')
    venue3 = create_venue(offerer, siret=offerer.siren + '54321', postal_code='93000', departement_code='93')
    offer1 = create_offer_with_event_product(venue1, event_type=EventType.ACTIVATION)
    offer2 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION)
    offer3 = create_offer_with_event_product(venue3, event_type=EventType.ACTIVATION)
    offer4 = create_offer_with_event_product(venue3, event_type=EventType.ACTIVATION)
    stock1 = create_stock_from_offer(offer1, price=0, available=0)
    stock2 = create_stock_from_offer(offer2, price=0, available=10)
    stock3 = create_stock_from_offer(offer3, price=0, available=1)
    booking = create_booking(create_user(), stock3, venue=venue3, quantity=1)
    PcObject.save(stock1, stock2, stock3, booking, offer4)

    # when
    offers = find_activation_offers('93').all()

    # then
    assert len(offers) == 1


@clean_database
def test_find_activation_offers_returns_activation_offers_with_future_booking_limit_datetime(app):
    # given
    now = datetime.utcnow()
    five_days_ago = now - timedelta(days=5)
    next_week = now + timedelta(days=7)
    offerer = create_offerer()
    venue1 = create_venue(offerer, siret=offerer.siren + '12345', postal_code='93000', departement_code='93')
    venue2 = create_venue(offerer, siret=offerer.siren + '67890', postal_code='93000', departement_code='93')
    venue3 = create_venue(offerer, siret=offerer.siren + '54321', postal_code='93000', departement_code='93')
    offer1 = create_offer_with_event_product(venue1, event_type=EventType.ACTIVATION)
    offer2 = create_offer_with_event_product(venue2, event_type=EventType.ACTIVATION)
    offer3 = create_offer_with_event_product(venue3, event_type=EventType.ACTIVATION)
    stock1 = create_stock_from_offer(offer1, price=0, booking_limit_datetime=five_days_ago)
    stock2 = create_stock_from_offer(offer2, price=0, booking_limit_datetime=next_week)
    stock3 = create_stock_from_offer(offer3, price=0, booking_limit_datetime=None)
    PcObject.save(stock1, stock2, stock3)

    # when
    offers = find_activation_offers('93').all()

    # then
    assert offer1 not in offers
    assert offer2 in offers
    assert offer3 in offers


@clean_database
def test_find_offers_with_filter_parameters_with_partial_keywords_and_filter_by_venue(app):
    user = create_user(email='offerer@email.com')
    offerer1 = create_offerer(siren='123456789')
    offerer2 = create_offerer(siren='987654321')
    ko_offerer3 = create_offerer(siren='123456780')
    user_offerer1 = create_user_offerer(user, offerer1)
    user_offerer2 = create_user_offerer(user, offerer2)

    ok_product_event = create_product_with_event_type(event_name='Rencontre avec Jacques Martin')
    ok_product_thing = create_product_with_thing_type(thing_name='Rencontrez Jacques Chirac')
    event_product2 = create_product_with_event_type(event_name='Concert de contrebasse')
    thing1_product = create_product_with_thing_type(thing_name='Jacques la fripouille')
    thing2_product = create_product_with_thing_type(thing_name='Belle du Seigneur')
    offerer = create_offerer()
    venue1 = create_venue(offerer1, name='Bataclan', city='Paris', siret=offerer.siren + '12345')
    venue2 = create_venue(offerer2, name='Librairie la Rencontre', city='Saint Denis', siret=offerer.siren + '54321')
    ko_venue3 = create_venue(ko_offerer3, name='Une librairie du méchant concurrent gripsou', city='Saint Denis',
                             siret=ko_offerer3.siren + '54321')
    ok_offer1 = create_offer_with_event_product(venue1, ok_product_event)
    ok_offer2 = create_offer_with_thing_product(venue1, ok_product_thing)
    ko_offer2 = create_offer_with_event_product(venue1, event_product2)
    ko_offer3 = create_offer_with_thing_product(ko_venue3, thing1_product)
    ko_offer4 = create_offer_with_thing_product(venue2, thing2_product)
    PcObject.save(
        user_offerer1, user_offerer2, ko_offerer3,
        ok_offer1, ko_offer2, ko_offer3, ko_offer4
    )

    # when
    offers = find_offers_with_filter_parameters(
        user,
        venue_id=venue1.id,
        keywords_string='Jacq Rencon'
    ).all()

    # then
    offers_id = [offer.id for offer in offers]
    assert ok_offer1.id in offers_id
    assert ok_offer2.id in offers_id
    assert ko_offer2.id not in offers_id
    assert ko_offer3.id not in offers_id
    assert ko_offer4.id not in offers_id


@clean_database
def test_offer_remaining_stock_filter_does_not_filter_offer_with_cancelled_bookings(app):
    # Given
    product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
    offerer = create_offerer()
    venue = create_venue(offerer, postal_code='34000', departement_code='34')
    offer = create_offer_with_thing_product(venue, product)
    stock = create_stock_from_offer(offer, available=2)
    booking = create_booking(create_user(), stock, venue=venue, quantity=2, is_cancelled=True)
    PcObject.save(booking)

    # When
    nb_offers_with_remaining_stock = Offer.query \
        .join(Stock) \
        .filter(_build_has_remaining_stock_predicate()) \
        .count()

    # Then
    assert nb_offers_with_remaining_stock == 1


@clean_database
def test_offer_remaining_stock_filter_filters_offer_with_no_remaining_stock(app):
    # Given
    product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
    offerer = create_offerer()
    venue = create_venue(offerer, postal_code='34000', departement_code='34')
    offer = create_offer_with_thing_product(venue, product)
    stock = create_stock_from_offer(offer, available=2, price=0)
    user = create_user()
    booking1 = create_booking(user, stock, venue=venue, quantity=2, is_cancelled=True)
    booking2 = create_booking(user, stock, venue=venue, quantity=2)
    PcObject.save(booking1, booking2)

    # When
    nb_offers_with_remaining_stock = Offer.query \
        .join(Stock) \
        .filter(_build_has_remaining_stock_predicate()) \
        .count()

    # Then
    assert nb_offers_with_remaining_stock == 0


@clean_database
def test_offer_remaining_stock_filter_filters_offer_with_one_full_stock_and_one_empty_stock(app):
    # Given
    product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
    offerer = create_offerer()
    venue = create_venue(offerer, postal_code='34000', departement_code='34')
    offer = create_offer_with_thing_product(venue, product)
    stock1 = create_stock_from_offer(offer, available=2, price=0)
    stock2 = create_stock_from_offer(offer, available=2, price=0)
    user = create_user()
    booking1 = create_booking(user, stock1, venue=venue, quantity=2)
    PcObject.save(booking1, stock2)

    # When
    nb_offers_with_remaining_stock = Offer.query \
        .join(Stock) \
        .filter(_build_has_remaining_stock_predicate()) \
        .count()

    # Then
    assert nb_offers_with_remaining_stock == 1


@clean_database
def test_find_offers_by_venue_id_return_offers_matching_venue_id(app):
    # Given
    product = create_product_with_thing_type(thing_name='Lire un livre', is_national=True)
    offerer = create_offerer()
    venue = create_venue(offerer, postal_code='34000', departement_code='34')
    offer = create_offer_with_thing_product(venue, product)
    PcObject.save(offer)

    # When
    offers = find_offers_by_venue_id(venue.id)

    # Then
    assert len(offers) == 1
    assert offers[0].venueId == venue.id


def _create_event_stock_and_offer_for_date(venue, date):
    product = create_product_with_event_type()
    offer = create_offer_with_event_product(venue, product)
    event_occurrence = create_event_occurrence(offer, beginning_datetime=date, end_datetime=date + timedelta(hours=1))
    stock = create_stock_from_event_occurrence(event_occurrence, booking_limit_date=date)
    return stock


@pytest.mark.standalone
class BaseScoreTest:

    @clean_database
    def test_order_by_base_score(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        criterion_negative = create_criterion(name='negative', score_delta=-1)
        criterion_positive = create_criterion(name='positive', score_delta=1)

        offer1 = create_offer_with_thing_product(venue)
        offer2 = create_offer_with_thing_product(venue)

        offer1.criteria = [criterion_negative]
        offer2.criteria = [criterion_negative, criterion_positive]

        PcObject.save(offer1, offer2)

        # When
        offers = Offer.query \
            .order_by(Offer.baseScore.desc()) \
            .all()

        # Then
        assert offers == [offer2, offer1]


@pytest.mark.standalone
class GetActiveOffersTest:
    @clean_database
    def test_get_active_offers_with_no_order_by_should_return_same_number_of_recos(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        stock1 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock2 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock3 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.AUDIOVISUEL)
        stock4 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.JEUX)

        PcObject.save(stock1, stock2, stock3, stock4)

        # When
        offers = get_active_offers(departement_codes=['00'],
                                   offer_id=None)

        # Then
        assert len(offers) == 4

    @clean_database
    def test_get_active_offers_with_criteria_should_return_offer_with_highest_base_score_first(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        offer1 = create_offer_with_thing_product(venue, thing_type=ThingType.JEUX_VIDEO, thumb_count=1)
        stock1 = create_stock_from_offer(offer1, price=0)
        offer1.criteria = [create_criterion(name='negative', score_delta=-1)]

        offer2 = create_offer_with_thing_product(venue, thing_type=ThingType.JEUX_VIDEO, thumb_count=1)
        stock2 = create_stock_from_offer(offer2, price=0)
        offer2.criteria = [create_criterion(name='positive', score_delta=1)]

        PcObject.save(stock1, stock2)

        # When
        offers = get_active_offers(departement_codes=['00'],
                                   offer_id=None,
                                   order_by=order_by_with_criteria)

        # Then
        assert offers == [offer2, offer1]

    @clean_database
    def test_get_active_offers_with_criteria_should_return_offer_with_highest_base_score_first_bust_keep_the_partition(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000', departement_code='34')

        offer1 = create_offer_with_thing_product(venue, thing_type=ThingType.CINEMA_ABO, thumb_count=1)
        stock1 = create_stock_from_offer(offer1, price=0)
        offer1.criteria = [create_criterion(name='negative', score_delta=1)]

        offer2 = create_offer_with_thing_product(venue, thing_type=ThingType.CINEMA_ABO, thumb_count=1)
        stock2 = create_stock_from_offer(offer2, price=0)
        offer2.criteria = [create_criterion(name='positive', score_delta=2)]

        offer3 = create_offer_with_thing_product(venue, thing_type=ThingType.JEUX_VIDEO, thumb_count=1)
        stock3 = create_stock_from_offer(offer3, price=0)
        offer3.criteria = []

        PcObject.save(stock1, stock2, stock3)

        # When
        offers = get_active_offers(departement_codes=['00'],
                                   offer_id=None,
                                   order_by=order_by_with_criteria)

        # Then
        assert offers == [offer2, offer3, offer1]
