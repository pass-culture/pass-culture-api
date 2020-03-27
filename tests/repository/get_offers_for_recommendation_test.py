from datetime import datetime, timedelta

from models import DiscoveryView
from models.offer_type import EventType, ThingType
from repository import repository
from repository.offer_queries import get_offers_for_recommendation
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_booking, create_criterion, create_user, create_offerer, \
    create_venue, \
    create_favorite, create_mediation
from tests.model_creators.specific_creators import create_stock_with_event_offer, create_stock_from_offer, \
    create_stock_with_thing_offer, create_product_with_thing_type, \
    create_offer_with_thing_product, create_offer_with_event_product

REFERENCE_DATE = '2017-10-15 09:21:34'


class GetOfferForRecommendationsTest:
    @clean_database
    def test_when_department_code_00_should_return_offers_of_all_departements(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        user = create_user()
        venue_34 = create_venue(offerer, postal_code='34000',
                                departement_code='34', siret=offerer.siren + '11111')
        venue_93 = create_venue(offerer, postal_code='93000',
                                departement_code='93', siret=offerer.siren + '22222')
        venue_75 = create_venue(offerer, postal_code='75000',
                                departement_code='75', siret=offerer.siren + '33333')
        offer_34 = create_offer_with_thing_product(venue_34)
        offer_93 = create_offer_with_thing_product(venue_93)
        offer_75 = create_offer_with_thing_product(venue_75)
        stock_34 = create_stock_from_offer(offer_34)
        stock_93 = create_stock_from_offer(offer_93)
        stock_75 = create_stock_from_offer(offer_75)
        create_mediation(stock_34.offer)
        create_mediation(stock_93.offer)
        create_mediation(stock_75.offer)

        repository.save(user, stock_34, stock_93, stock_75)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offer_34 in offers
        assert offer_93 in offers
        assert offer_75 in offers

    @clean_database
    def test_should_return_offer_when_offer_is_national(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        user = create_user()
        venue_34 = create_venue(offerer, postal_code='34000',
                                departement_code='34', siret=offerer.siren + '11111')
        offer_34 = create_offer_with_thing_product(venue_34)
        offer_national = create_offer_with_thing_product(
            venue_34, is_national=True)
        stock_34 = create_stock_from_offer(offer_34)
        stock_national = create_stock_from_offer(offer_national)
        create_mediation(stock_34.offer)
        create_mediation(stock_national.offer)

        repository.save(user, stock_34, stock_national)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['93'],
                                               user=user)

        # Then
        assert offer_34 not in offers
        assert offer_national in offers

    @clean_database
    def test_should_not_return_activation_event(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        user = create_user()
        venue_93 = create_venue(offerer, postal_code='93000',
                                departement_code='93', siret=offerer.siren + '33333')
        offer_93 = create_offer_with_event_product(venue_93, thumb_count=1)
        offer_activation_93 = create_offer_with_event_product(venue_93, event_type=EventType.ACTIVATION,
                                                              thumb_count=1)
        stock_93 = create_stock_from_offer(offer_93)
        stock_activation_93 = create_stock_from_offer(offer_activation_93)
        mediation1 = create_mediation(stock_93.offer)
        mediation2 = create_mediation(stock_activation_93.offer)

        repository.save(user, stock_93, stock_activation_93,
                        mediation1, mediation2)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offer_93 in offers
        assert offer_activation_93 not in offers

    @clean_database
    def test_should_not_return_activation_thing(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        user = create_user()
        venue_93 = create_venue(offerer, postal_code='93000',
                                departement_code='93', siret=offerer.siren + '33333')
        offer_93 = create_offer_with_thing_product(venue_93, thumb_count=1)
        offer_activation_93 = create_offer_with_thing_product(venue_93, thing_type=ThingType.ACTIVATION,
                                                              thumb_count=1)
        stock_93 = create_stock_from_offer(offer_93)
        stock_activation_93 = create_stock_from_offer(offer_activation_93)
        create_mediation(stock_93.offer)
        create_mediation(stock_activation_93.offer)

        repository.save(user, stock_93, stock_activation_93)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offer_93 in offers
        assert offer_activation_93 not in offers

    @clean_database
    def test_should_return_offers_with_stock(self, app):
        # Given
        product = create_product_with_thing_type(
            thing_name='Lire un livre', is_national=True)
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')
        offer = create_offer_with_thing_product(venue=venue, product=product)
        stock = create_stock_from_offer(offer, available=2)
        create_mediation(stock.offer)
        repository.save(user, stock)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert len(offers) == 1

    @clean_database
    def test_should_return_offers_with_mediation_only(app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')
        stock1 = create_stock_with_thing_offer(
            offerer, venue, name='thing_with_mediation')
        stock2 = create_stock_with_thing_offer(
            offerer, venue, name='thing_without_mediation')
        create_mediation(stock1.offer)
        repository.save(user, stock1, stock2)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert len(offers) == 1
        assert offers[0].name == 'thing_with_mediation'

    @clean_database
    def test_should_return_offers_that_occur_in_less_than_10_days_and_things_first(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

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
        create_mediation(stock1.offer)
        create_mediation(stock2.offer)
        create_mediation(stock3.offer)
        repository.save(user, stock1, stock2, stock3)

        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert len(offers) == 3
        assert (offers[0].name == 'event_occurs_soon'
                and offers[1].name == 'thing') \
            or (offers[1].name == 'event_occurs_soon'
                and offers[0].name == 'thing')
        assert offers[2].name == 'event_occurs_later'

    @clean_database
    def test_should_return_offers_with_varying_types(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')
        stock1 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock2 = create_stock_with_thing_offer(offerer, venue, name='thing', thing_type=ThingType.CINEMA_ABO,
                                               url='http://example.com')
        stock3 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock4 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock5 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.AUDIOVISUEL)
        stock6 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX)
        create_mediation(stock1.offer)
        create_mediation(stock2.offer)
        create_mediation(stock3.offer)
        create_mediation(stock4.offer)
        create_mediation(stock5.offer)
        create_mediation(stock6.offer)
        repository.save(user, stock1, stock2, stock3, stock4, stock5, stock6)
        DiscoveryView.refresh(concurrently=False)

        def _first_four_offers_have_different_type_and_onlineness(offers):
            return len(set([o.type + (o.url or '')
                            for o in offers[:4]])) == 4

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert len(offers) == 6
        assert _first_four_offers_have_different_type_and_onlineness(offers)

    @clean_database
    def test_should_not_return_offers_with_no_stock(self, app):
        # Given
        product = create_product_with_thing_type(
            thing_name='Lire un livre', is_national=True)
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')
        offer = create_offer_with_thing_product(venue=venue, product=product)
        stock = create_stock_from_offer(offer, available=2, price=0)
        booking1 = create_booking(
            user=user, stock=stock, is_cancelled=True, quantity=2, venue=venue)
        booking2 = create_booking(
            user=user, stock=stock, quantity=2, venue=venue)
        create_mediation(stock.offer)
        repository.save(user, booking1, booking2)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert len(offers) == 0

    @clean_database
    def test_should_return_same_number_of_offers(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

        stock1 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock2 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX_VIDEO)
        stock3 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.AUDIOVISUEL)
        stock4 = create_stock_with_thing_offer(
            offerer, venue, name='thing', thing_type=ThingType.JEUX)
        create_mediation(stock1.offer)
        create_mediation(stock2.offer)
        create_mediation(stock3.offer)
        create_mediation(stock4.offer)

        repository.save(user, stock1, stock2, stock3, stock4)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert len(offers) == 4

    @clean_database
    def test_with_criteria_should_return_offer_with_highest_base_score_first(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

        offer1 = create_offer_with_thing_product(
            venue, thing_type=ThingType.JEUX_VIDEO, thumb_count=1)
        stock1 = create_stock_from_offer(offer1, price=0)
        offer1.criteria = [create_criterion(name='negative', score_delta=-1)]

        offer2 = create_offer_with_thing_product(
            venue, thing_type=ThingType.JEUX_VIDEO, thumb_count=1)
        stock2 = create_stock_from_offer(offer2, price=0)
        offer2.criteria = [create_criterion(name='positive', score_delta=1)]

        create_mediation(stock1.offer)
        create_mediation(stock2.offer)

        repository.save(user, stock1, stock2)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offers == [offer2, offer1]

    @clean_database
    def test_with_criteria_should_return_offer_with_highest_base_score_first_bust_keep_the_partition(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

        offer1 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO, thumb_count=1)
        stock1 = create_stock_from_offer(offer1, price=0)
        offer1.criteria = [create_criterion(name='negative', score_delta=1)]

        offer2 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO, thumb_count=1)
        stock2 = create_stock_from_offer(offer2, price=0)
        offer2.criteria = [create_criterion(name='positive', score_delta=2)]

        offer3 = create_offer_with_thing_product(
            venue, thing_type=ThingType.JEUX_VIDEO, thumb_count=1)
        stock3 = create_stock_from_offer(offer3, price=0)
        offer3.criteria = []

        create_mediation(stock1.offer)
        create_mediation(stock2.offer)
        create_mediation(stock3.offer)

        repository.save(user, stock1, stock2, stock3)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offers == [offer2, offer3, offer1]

    @clean_database
    def test_should_return_offers_in_the_same_order_given_the_same_seed(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

        offer1 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock1 = create_stock_from_offer(offer1, price=0)

        offer2 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock2 = create_stock_from_offer(offer2, price=0)

        offer3 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock3 = create_stock_from_offer(offer3, price=0)

        offer4 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock4 = create_stock_from_offer(offer4, price=0)

        create_mediation(stock1.offer)
        create_mediation(stock2.offer)
        create_mediation(stock3.offer)
        create_mediation(stock4.offer)

        repository.save(user, stock1, stock2, stock3, stock4)
        DiscoveryView.refresh(concurrently=False)

        pagination_params = {'seed': 0.5, 'page': 1}
        offers_1 = get_offers_for_recommendation(departement_codes=['00'],
                                                 user=user)

        offers_2 = get_offers_for_recommendation(departement_codes=['00'],
                                                 user=user)

        offers_3 = get_offers_for_recommendation(departement_codes=['00'],
                                                 user=user)

        # When
        offers_4 = get_offers_for_recommendation(departement_codes=['00'],
                                                 user=user)

        # Then
        assert offers_1 == offers_4
        assert offers_2 == offers_4
        assert offers_3 == offers_4

    @clean_database
    def test_should_return_offers_not_in_the_same_order_given_different_seeds(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

        offer1 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock1 = create_stock_from_offer(offer1, price=0)

        offer2 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock2 = create_stock_from_offer(offer2, price=0)

        offer3 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock3 = create_stock_from_offer(offer3, price=0)

        offer4 = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock4 = create_stock_from_offer(offer4, price=0)

        create_mediation(stock1.offer)
        create_mediation(stock2.offer)
        create_mediation(stock3.offer)
        create_mediation(stock4.offer)

        repository.save(user, stock1, stock2, stock3, stock4)
        DiscoveryView.refresh(concurrently=False)

        offers_1 = get_offers_for_recommendation(departement_codes=['00'],
                                                 user=user)

        DiscoveryView.refresh()

        # When
        offers_2 = get_offers_for_recommendation(departement_codes=['00'],
                                                 user=user,
                                                 seen_recommendation_ids=[offer.id for offer in offers_1])

        # Then
        assert offers_1 != offers_2

    @clean_database
    def test_should_not_return_booked_offers(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')
        offer = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock = create_stock_from_offer(offer, price=0)
        user = create_user()
        booking = create_booking(user=user, stock=stock)
        create_mediation(stock.offer)
        repository.save(user, booking)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offers == []

    @clean_database
    def test_should_not_return_favorite_offers(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer, postal_code='34000',
                             departement_code='34')

        offer = create_offer_with_thing_product(
            venue, thing_type=ThingType.CINEMA_ABO)
        stock = create_stock_from_offer(offer, price=0)
        mediation = create_mediation(stock.offer)
        favorite = create_favorite(mediation=mediation, offer=offer, user=user)

        repository.save(user, favorite)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               user=user)

        # Then
        assert offers == []

    @clean_database
    def test_should_return_different_offers_when_different_page_and_same_seed(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(idx=1, venue=venue)
        offer2 = create_offer_with_thing_product(idx=2, venue=venue)
        offer3 = create_offer_with_thing_product(idx=3, venue=venue)
        offer4 = create_offer_with_thing_product(idx=4, venue=venue)
        stock1 = create_stock_from_offer(offer1)
        stock2 = create_stock_from_offer(offer2)
        stock3 = create_stock_from_offer(offer3)
        stock4 = create_stock_from_offer(offer4)
        create_mediation(offer1)
        create_mediation(offer2)
        create_mediation(offer3)
        create_mediation(offer4)
        repository.save(user, stock1, stock2, stock3, stock4)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers1 = get_offers_for_recommendation(departement_codes=['00'],
                                                limit=2,
                                                user=user)
        offers2 = get_offers_for_recommendation(departement_codes=['00'],
                                                limit=2,
                                                user=user,
                                                seen_recommendation_ids=[offer.id for offer in offers1])
        offers3 = get_offers_for_recommendation(departement_codes=['00'],
                                                limit=2,
                                                user=user,
                                                seen_recommendation_ids=[offer.id for offer in offers1 + offers2])

        # Then
        assert len(offers1) == 2
        assert offers1 != offers2
        assert len(offers2) == 2
        assert len(offers3) == 0


    @clean_database
    def test_should_not_return_offer_with_no_remaining_quantity(self, app):
        # Given
        yesterday = datetime.utcnow() - timedelta(days=1)
        offerer = create_offerer()
        user = create_user()
        user_with_booking = create_user(email='has_bookings@example.com')
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(idx=1, venue=venue)
        stock = create_stock_from_offer(offer, available=2, price=0, date_modified=datetime.utcnow())
        booking = create_booking(user_with_booking, stock=stock, quantity=2, is_used=True, date_used=yesterday)
        mediation = create_mediation(offer)
        repository.save(user, booking, mediation)
        DiscoveryView.refresh(concurrently=False)

        # When
        offers = get_offers_for_recommendation(departement_codes=['00'],
                                               limit=2,
                                               user=user)

        # Then
        assert offers == []
