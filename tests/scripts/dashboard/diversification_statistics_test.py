from datetime import datetime, timedelta
from pprint import pprint

import pandas

from models import PcObject, EventType, ThingType
from scripts.dashboard.diversification_statistics import get_offerers_with_offer_available_on_discovery_count, \
    get_offerers_with_non_cancelled_bookings_count, get_offers_with_user_offerer_and_stock_count, \
    get_offers_available_on_discovery_count, get_offers_with_non_cancelled_bookings_count, \
    _query_get_offer_counts_grouped_by_type_and_medium, _get_offers_grouped_by_type_and_medium, \
    _get_offer_counts_grouped_by_type_and_medium, _query_get_booking_counts_grouped_by_type_and_medium, \
    get_offerer_count, get_offerer_with_stock_count, get_all_bookings_count, count_all_cancelled_bookings
from tests.conftest import clean_database
from tests.test_utils import create_user, create_offerer, create_user_offerer, create_stock, \
    create_offer_with_thing_product, create_venue, create_mediation, create_offer_with_event_product, create_booking

class GetOffererCountTest:
    @clean_database
    def test_counts_every_offerer_when_not_filtered(self, app):
        # Given
        first_user = create_user(email='first@example.net')
        first_offerer = create_offerer(siren='111111111')
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        create_user_offerer(first_user, first_offerer)

        second_user = create_user(email='second@example.net')
        second_offerer = create_offerer(siren='222222222')
        second_venue = create_venue(first_offerer, postal_code='37150', siret='22222222200002')
        create_user_offerer(second_user, second_offerer)
        PcObject.save(first_offerer, first_venue, second_offerer, second_venue)

        # When
        number_of_offerers = get_offerer_count()

        # Then
        assert number_of_offerers == 2

    @clean_database
    def test_counts_offerer_in_departement_when_filtered(self, app):
        # Given
        first_user = create_user(email='first@example.net')
        first_offerer = create_offerer(siren='111111111')
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        create_user_offerer(first_user, first_offerer)

        second_user = create_user(email='second@example.net')
        second_offerer = create_offerer(siren='222222222')
        second_venue = create_venue(first_offerer, postal_code='37150', siret='22222222200002')
        create_user_offerer(second_user, second_offerer)
        PcObject.save(first_offerer, first_venue, second_offerer, second_venue)

        # When
        number_of_offerers = get_offerer_count('37')

        # Then
        assert number_of_offerers == 1


class GetOffererCountWithStockTest:
    @clean_database
    def test_counts_every_offerer_when_not_filtered(self, app):
        # Given
        first_user = create_user(email='first@example.net')
        first_offerer = create_offerer(siren='111111111')
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_stock = create_stock(offer=first_offer)
        first_user_offerer = create_user_offerer(first_user, first_offerer)

        second_user = create_user(email='second@example.net')
        second_offerer = create_offerer(siren='222222222')
        second_venue = create_venue(second_offerer, postal_code='37150', siret='22222222200002')
        second_offer = create_offer_with_thing_product(second_venue)
        second_stock = create_stock(offer=second_offer)
        create_user_offerer(second_user, second_offerer)

        PcObject.save(first_offerer, first_venue, second_offerer, second_venue)

        # When
        number_of_offerers = get_offerer_with_stock_count()

        # Then
        assert number_of_offerers == 2

    @clean_database
    def test_counts_offerer_in_departement_when_filtered(self, app):
        # Given
        first_user = create_user(email='first@example.net')
        first_offerer = create_offerer(siren='111111111')
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_stock = create_stock(offer=first_offer)
        first_user_offerer = create_user_offerer(first_user, first_offerer)

        second_user = create_user(email='second@example.net')
        second_offerer = create_offerer(siren='222222222')
        second_venue = create_venue(second_offerer, postal_code='37150', siret='22222222200002')
        second_offer = create_offer_with_thing_product(second_venue)
        second_stock = create_stock(offer=second_offer)
        create_user_offerer(second_user, second_offerer)

        PcObject.save(first_offerer, first_venue, second_offerer, second_venue)

        # When
        number_of_offerers = get_offerer_with_stock_count('37')

        # Then
        assert number_of_offerers == 1


class GetOfferersWithOfferAvailableOnDiscoveryCountTest:
    @clean_database
    def test_returns_0_if_only_offerer_with_inactive_offer(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=False)
        mediation = create_mediation(offer)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_only_offerer_with_offer_without_stock(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True)
        mediation = create_mediation(offer)
        PcObject.save(offer)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_only_offerer_with_unvalidated_venue(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_thing_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        mediation = create_mediation(offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_only_offerer_without_mediation(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_thing_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_stock_passed(self, app):
        # Given
        yesterday = datetime.utcnow() - timedelta(days=1)
        offerer = create_offerer()
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_event_product(venue, is_active=True)
        stock = create_stock(offer=offer, beginning_datetime=yesterday)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_offerer_not_active(self, app):
        # Given
        offerer = create_offerer(is_active=False)
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_event_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_offerer_not_validated(self, app):
        # Given
        offerer = create_offerer(validation_token='XDFCGHVJBKNL')
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_event_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_0_if_only_offerer_with_activation_offer(self, app):
        # Given
        offerer = create_offerer(validation_token='XDFCGHVJBKNL')
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_thing_product(venue, is_active=True, thing_type='ThingType.ACTIVATION')
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_1_if_offerer_with_offer_returned_by_get_active_offers(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        mediation = create_mediation(offer)
        PcObject.save(stock)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 1

    @clean_database
    def test_returns_1_if_offerer_with_2_offers_returned_by_get_active_offers(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue, is_active=True)
        offer2 = create_offer_with_thing_product(venue, is_active=True)
        stock1 = create_stock(offer=offer1)
        stock2 = create_stock(offer=offer2)
        mediation1 = create_mediation(offer1)
        mediation2 = create_mediation(offer2)
        PcObject.save(stock1, stock2, offer2)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count()

        # Then
        assert number_of_offerers == 1

    @clean_database
    def test_counts_only_offeres_with_venues_in_the_departement_when_filtered_by_departement_code(self, app):
        # Given
        first_user = create_user(email='first@example.net')
        first_offerer = create_offerer(siren='111111111')
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_stock = create_stock(offer=first_offer)
        first_user_offerer = create_user_offerer(first_user, first_offerer)
        mediation1 = create_mediation(first_offer)

        second_user = create_user(email='second@example.net')
        second_offerer = create_offerer(siren='222222222')
        second_venue = create_venue(second_offerer, postal_code='37150', siret='22222222200002')
        second_offer = create_offer_with_thing_product(second_venue)
        second_stock = create_stock(offer=second_offer)
        create_user_offerer(second_user, second_offerer)
        mediation2 = create_mediation(second_offer)

        PcObject.save(first_offerer, first_venue, second_offerer, second_venue)

        # When
        number_of_offerers = get_offerers_with_offer_available_on_discovery_count('76')

        # Then
        assert number_of_offerers == 1


class GetOfferersWithNonCancelledBookingsCountTest:
    @clean_database
    def test_returns_0_if_no_bookings(self, app):
        # Given
        offerer = create_offerer()
        PcObject.save(offerer)

        # When
        number_of_offerers = get_offerers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offerers == 0

    @clean_database
    def test_returns_1_if_offerer_with_non_cancelled_booking(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)
        user = create_user()
        booking = create_booking(user, stock)
        PcObject.save(booking)

        # When
        number_of_offerers = get_offerers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offerers == 1

    @clean_database
    def test_returns_1_if_offerer_with_2_non_cancelled_bookings(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer, price=0)
        stock2 = create_stock(offer=offer, price=0)
        user = create_user()
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        PcObject.save(booking1, booking2)

        # When
        number_of_offerers = get_offerers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offerers == 1

    @clean_database
    def test_returns_0_when_venue_is_in_the_wrong_departement(self, app):
        # Given
        user = create_user()

        first_offerer = create_offerer(siren='111111111')
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_stock = create_stock(offer=first_offer, price=0)
        first_booking = create_booking(user, first_stock)

        second_offerer = create_offerer(siren='222222222')
        second_venue = create_venue(second_offerer, postal_code='41571', siret='22222222200001')
        second_offer = create_offer_with_thing_product(second_venue)
        second_stock = create_stock(offer=second_offer, price=0)
        second_booking = create_booking(user, second_stock)

        PcObject.save(first_booking, second_booking)

        # When
        number_of_offerers = get_offerers_with_non_cancelled_bookings_count('41')

        # Then
        assert number_of_offerers == 1

    @clean_database
    def test_returns_0_if_offerer_with_cancelled_bookings(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)
        user = create_user()
        booking = create_booking(user, stock, is_cancelled=True)
        PcObject.save(booking)

        # When
        number_of_offerers = get_offerers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offerers == 0


class GetOffersWithUserOffererAndStockCountTest:
    @clean_database
    def test_returns_0_if_offer_without_user_offerer(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_with_user_offerer_and_stock_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_1_if_offer_with_user_offerer_and_stock(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_offerer = create_user_offerer(user, offerer)
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer)
        PcObject.save(stock, user_offerer)

        # When
        number_of_offers = get_offers_with_user_offerer_and_stock_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_0_if_offer_without_stock(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_offerer = create_user_offerer(user, offerer)
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        PcObject.save(user_offerer)

        # When
        number_of_offers = get_offers_with_user_offerer_and_stock_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_1_if_offer_with_2_user_offerer_and_stock(self, app):
        # Given
        offerer = create_offerer()
        user1 = create_user()
        user2 = create_user(email='other@email.com')
        user_offerer1 = create_user_offerer(user1, offerer)
        user_offerer2 = create_user_offerer(user2, offerer)
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer)
        PcObject.save(stock, user_offerer1)

        # When
        number_of_offers = get_offers_with_user_offerer_and_stock_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_1_if_offer_with_user_offerer_and_2_stocks(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_offerer = create_user_offerer(user, offerer)
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer)
        stock2 = create_stock(offer=offer)
        PcObject.save(stock1, stock2, user_offerer)

        # When
        number_of_offers = get_offers_with_user_offerer_and_stock_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_1_when_two_offerers_but_filtered_by_departement(self, app):
        # Given
        first_user = create_user(email='user76@example.net')
        first_offerer = create_offerer(siren='111111111')
        create_user_offerer(first_user, first_offerer)
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_stock = create_stock(offer=first_offer, price=0)

        second_user = create_user()
        second_offerer = create_offerer(siren='222222222')
        create_user_offerer(second_user, second_offerer)
        second_venue = create_venue(second_offerer, postal_code='41571', siret='22222222200001')
        second_offer = create_offer_with_thing_product(second_venue)
        second_stock = create_stock(offer=second_offer, price=0)

        PcObject.save(first_stock, second_stock)

        # When
        number_of_offers = get_offers_with_user_offerer_and_stock_count('76')

        # Then
        assert number_of_offers == 1


class GetOffersAvailableOnDiscoveryCountTest:
    @clean_database
    def test_returns_0_if_only_offerer_with_inactive_offer(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=False)
        mediation = create_mediation(offer)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_0_if_only_offerer_with_offer_without_stock(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True)
        mediation = create_mediation(offer)
        PcObject.save(offer)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_0_if_only_offerer_with_unvalidated_venue(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, validation_token='XDFCGHVJBK')
        offer = create_offer_with_thing_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        mediation = create_mediation(offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_1_if_only_offerer_without_mediation(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_0_if_only_offerer_without_mediation_and_thumb_count(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True, thumb_count=0)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_0_if_stock_passed(self, app):
        # Given
        yesterday = datetime.utcnow() - timedelta(days=1)
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_active=True)
        stock = create_stock(offer=offer, beginning_datetime=yesterday)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_0_if_offerer_not_active(self, app):
        # Given
        offerer = create_offerer(is_active=False)
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_0_if_offerer_not_validated(self, app):
        # Given
        offerer = create_offerer(validation_token='XDFCGHVJBKNL')
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_0_if_only_offerer_with_activation_offer(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True, thing_type=str(ThingType.ACTIVATION))
        stock = create_stock(offer=offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_1_if_offerer_with_offer_returned_by_get_active_offers(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=True)
        stock = create_stock(offer=offer)
        mediation = create_mediation(offer)
        PcObject.save(stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_2_if_2_offers_returned_by_get_active_offers(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue, is_active=True)
        offer2 = create_offer_with_thing_product(venue, is_active=True)
        stock1 = create_stock(offer=offer1)
        stock2 = create_stock(offer=offer2)
        mediation1 = create_mediation(offer1)
        mediation2 = create_mediation(offer2)
        PcObject.save(stock1, stock2)

        # When
        number_of_offers = get_offers_available_on_discovery_count()

        # Then
        assert number_of_offers == 2

    @clean_database
    def test_returns_1_if_2_offers_returned_by_get_active_offers_but_only_one_in_departement(self, app):
        # Given
        first_user = create_user(email='user76@example.net')
        first_offerer = create_offerer(siren='111111111')
        create_user_offerer(first_user, first_offerer)
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_mediation = create_mediation(first_offer)
        first_stock = create_stock(offer=first_offer, price=0)

        second_user = create_user(email='user41@example.net')
        second_offerer = create_offerer(siren='222222222')
        create_user_offerer(second_user, second_offerer)
        second_venue = create_venue(second_offerer, postal_code='41571', siret='22222222200001')
        second_offer = create_offer_with_thing_product(second_venue)
        second_mediation = create_mediation(second_offer)
        second_stock = create_stock(offer=second_offer, price=0)

        PcObject.save(first_stock, second_stock)

        # When
        number_of_offers = get_offers_available_on_discovery_count('41')

        # Then
        assert number_of_offers == 1


class GetOffersWithNonCancelledBookingsCountTest:
    @clean_database
    def test_returns_0_if_no_bookings(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        PcObject.save(offer)

        # When
        number_of_offers = get_offers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offers == 0

    @clean_database
    def test_returns_1_if_offer_with_non_cancelled_booking(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)
        user = create_user()
        booking = create_booking(user, stock)
        PcObject.save(booking)

        # When
        number_of_offers = get_offers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_1_if_offer_with_2_non_cancelled_bookings(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer, price=0)
        stock2 = create_stock(offer=offer, price=0)
        user = create_user()
        booking1 = create_booking(user, stock1)
        booking2 = create_booking(user, stock2)
        PcObject.save(booking1, booking2)

        # When
        number_of_offers = get_offers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_1_if_two_offerers_with_effective_bookings_but_only_one_in_departement(self, app):
        # Given
        first_user = create_user(email='user76@example.net')
        first_offerer = create_offerer(siren='111111111')
        create_user_offerer(first_user, first_offerer)
        first_venue = create_venue(first_offerer, postal_code='76130', siret='11111111100001')
        first_offer = create_offer_with_thing_product(first_venue)
        first_stock = create_stock(offer=first_offer, price=0)

        second_user = create_user(email='user41@example.net')
        second_offerer = create_offerer(siren='222222222')
        create_user_offerer(second_user, second_offerer)
        second_venue = create_venue(second_offerer, postal_code='41571', siret='22222222200001')
        second_offer = create_offer_with_thing_product(second_venue)
        second_stock = create_stock(offer=second_offer, price=0)

        user_with_bookings = create_user()
        booking1 = create_booking(user_with_bookings, first_stock)
        booking2 = create_booking(user_with_bookings, second_stock)

        PcObject.save(first_stock, second_stock, booking1, booking2)

        # When
        number_of_offers = get_offers_with_non_cancelled_bookings_count('41')

        # Then
        assert number_of_offers == 1

    @clean_database
    def test_returns_0_if_offerer_with_cancelled_bookings(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)
        user = create_user()
        booking = create_booking(user, stock, is_cancelled=True)
        PcObject.save(booking)

        # When
        number_of_offerers = get_offers_with_non_cancelled_bookings_count()

        # Then
        assert number_of_offerers == 0


class GetAllBookingsCount:
    @clean_database
    def test_counts_all_bookings(self, app):
        # Given
        user_in_76 = create_user(departement_code='76', email='user-76@example.net')
        user_in_41 = create_user(departement_code='41', email='user-41@example.net')

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)

        booking1 = create_booking(user_in_76, stock)
        booking2 = create_booking(user_in_41, stock, is_cancelled=True)
        PcObject.save(booking1, booking2)

        # When
        number_of_bookings = get_all_bookings_count()

        # Then
        assert number_of_bookings == 2

    @clean_database
    def test_counts_all_bookings(self, app):
        # Given
        user_in_76 = create_user(departement_code='76', email='user-76@example.net')
        user_in_41 = create_user(departement_code='41', email='user-41@example.net')

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)

        booking1 = create_booking(user_in_76, stock)
        booking2 = create_booking(user_in_41, stock, is_cancelled=True)
        PcObject.save(booking1, booking2)

        # When
        number_of_bookings = get_all_bookings_count('41')

        # Then
        assert number_of_bookings == 1


class QueryGetOfferCountsPerTypeAndMediumTest:
    @clean_database
    def test_returns_2_cinema_physical_1_musique_physical_and_1_musique_digital_when_offers_with_stock_and_user_offerer(
            self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_offerer = create_user_offerer(user, offerer)
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        stock_cinema1 = create_stock(offer=offer_cinema1)
        stock_cinema2 = create_stock(offer=offer_cinema2)
        stock_musique_digital = create_stock(offer=offer_musique_digital)
        stock_musique_physical = create_stock(offer=offer_musique_physical)
        PcObject.save(stock_cinema1, stock_cinema2, stock_musique_digital, stock_musique_physical, user_offerer)

        # When
        offer_counts = _query_get_offer_counts_grouped_by_type_and_medium().fetchall()

        # Then
        assert len(offer_counts) == 3
        assert ('EventType.CINEMA', False, 2) in offer_counts
        assert ('ThingType.MUSIQUE', False, 1) in offer_counts
        assert ('ThingType.MUSIQUE', True, 1) in offer_counts

    @clean_database
    def test_returns_nothing_when_no_stock(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_offerer = create_user_offerer(user, offerer)
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        PcObject.save(offer_cinema1, offer_cinema2, offer_musique_digital, offer_musique_physical, user_offerer)

        # When
        offer_counts = _query_get_offer_counts_grouped_by_type_and_medium().fetchall()

        # Then
        assert offer_counts == []

    @clean_database
    def test_returns_nothing_if_no_user_offerer(self, app):
        # Given
        offerer = create_offerer()
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        stock_cinema1 = create_stock(offer=offer_cinema1)
        stock_cinema2 = create_stock(offer=offer_cinema2)
        stock_musique_digital = create_stock(offer=offer_musique_digital)
        stock_musique_physical = create_stock(offer=offer_musique_physical)
        PcObject.save(stock_cinema1, stock_cinema2, stock_musique_digital, stock_musique_physical)

        # When
        offer_counts = _query_get_offer_counts_grouped_by_type_and_medium().fetchall()

        # Then
        assert offer_counts == []


class GetOffersByTypeAndDigitalTableTest:
    @clean_database
    def test_returns_table_with_columns_type_and_digital_ordered_by_type_then_digital(self, app):
        # Given
        expected_dataframe = pandas.read_csv('tests/scripts/dashboard/offers_by_type_and_digital.csv')

        # When
        type_and_digital_dataframe = _get_offers_grouped_by_type_and_medium()

        # Then
        pprint(expected_dataframe)
        assert type_and_digital_dataframe.equals(expected_dataframe)


class GetCountsByTypeAndDigitalCountsTest:
    @clean_database
    def test_returns_offers_ordered_by_counts_then_type_name_then_support(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_offerer = create_user_offerer(user, offerer)
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        stock_cinema1 = create_stock(offer=offer_cinema1)
        stock_cinema2 = create_stock(offer=offer_cinema2)
        stock_musique_digital = create_stock(offer=offer_musique_digital)
        stock_musique_physical = create_stock(offer=offer_musique_physical)
        PcObject.save(stock_cinema1, stock_cinema2, stock_musique_digital, stock_musique_physical, user_offerer)

        expected_dataframe = pandas.read_csv('tests/scripts/dashboard/offers_by_type_and_digital_counts.csv')

        # When
        offers_by_type_and_digital_counts = _get_offer_counts_grouped_by_type_and_medium(
            _query_get_offer_counts_grouped_by_type_and_medium,
            'Nombre d\'offres')

        # Then
        assert offers_by_type_and_digital_counts.eq(expected_dataframe).all().all()

    @clean_database
    def test_returns_bookings_ordered_by_counts_then_type_name_then_support(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_booking = create_user(email='booking@test.com')
        user_offerer = create_user_offerer(user, offerer)
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        stock_cinema1 = create_stock(offer=offer_cinema1, price=0)
        stock_cinema2 = create_stock(offer=offer_cinema2, price=0)
        stock_musique_digital = create_stock(offer=offer_musique_digital, price=0)
        stock_musique_physical = create_stock(offer=offer_musique_physical, price=0)
        booking_musique_physical1 = create_booking(user_booking, stock_musique_physical)
        booking_musique_physical2 = create_booking(user_booking, stock_musique_physical, quantity=2)
        booking_musique_digital = create_booking(user_booking, stock_musique_digital)
        PcObject.save(stock_cinema1, stock_cinema2, booking_musique_physical1, booking_musique_physical2,
                      booking_musique_digital, user_offerer)

        expected_dataframe = pandas.read_csv('tests/scripts/dashboard/bookings_by_type_and_medium_counts.csv')

        # When
        bookings_by_type_and_digital_counts = _get_offer_counts_grouped_by_type_and_medium(
            _query_get_booking_counts_grouped_by_type_and_medium, 'Nombre de réservations')

        # Then
        assert bookings_by_type_and_digital_counts.equals(expected_dataframe)


class QueryGetBookingCountsPerTypeAndDigitalTest:
    @clean_database
    def test_returns_3_musique_physical_1_musique_digital_when_bookings_with_user_offerer(
            self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_booking = create_user(email='booking@test.com')
        user_offerer = create_user_offerer(user, offerer)
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        stock_cinema1 = create_stock(offer=offer_cinema1, price=0)
        stock_cinema2 = create_stock(offer=offer_cinema2, price=0)
        stock_musique_digital = create_stock(offer=offer_musique_digital, price=0)
        stock_musique_physical = create_stock(offer=offer_musique_physical, price=0)
        booking_musique_physical1 = create_booking(user_booking, stock_musique_physical)
        booking_musique_physical2 = create_booking(user_booking, stock_musique_physical, quantity=2)
        booking_musique_digital = create_booking(user_booking, stock_musique_digital)
        PcObject.save(stock_cinema1, stock_cinema2, booking_musique_physical1, booking_musique_physical2,
                      booking_musique_digital, user_offerer)

        # When
        booking_counts = _query_get_booking_counts_grouped_by_type_and_medium().fetchall()

        # Then
        assert len(booking_counts) == 2
        assert ('ThingType.MUSIQUE', False, 3) in booking_counts
        assert ('ThingType.MUSIQUE', True, 1) in booking_counts

    @clean_database
    def test_returns_nothing_when_cancelled_booking(self, app):
        # Given
        offerer = create_offerer()
        user = create_user()
        user_booking = create_user(email='booking@test.com')
        user_offerer = create_user_offerer(user, offerer)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        stock = create_stock(offer=offer, price=0)
        cancelled_booking = create_booking(user_booking, stock, is_cancelled=True)
        PcObject.save(offer, user_offerer, cancelled_booking)

        # When
        booking_counts = _query_get_booking_counts_grouped_by_type_and_medium().fetchall()

        # Then
        assert booking_counts == []

    @clean_database
    def test_returns_nothing_if_no_user_offerer(self, app):
        # Given
        offerer = create_offerer()
        user_booking = create_user(email='booking@test.com')
        virtual_venue = create_venue(offerer, is_virtual=True, siret=None)
        physical_venue = create_venue(offerer, is_virtual=False)
        offer_cinema1 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_cinema2 = create_offer_with_event_product(physical_venue, event_type=EventType.CINEMA)
        offer_musique_digital = create_offer_with_thing_product(virtual_venue, url='http://url.test',
                                                                thing_type=ThingType.MUSIQUE)
        offer_musique_physical = create_offer_with_thing_product(physical_venue, thing_type=ThingType.MUSIQUE)
        stock_cinema1 = create_stock(offer=offer_cinema1, price=0)
        stock_cinema2 = create_stock(offer=offer_cinema2, price=0)
        stock_musique_digital = create_stock(offer=offer_musique_digital, price=0)
        stock_musique_physical = create_stock(offer=offer_musique_physical, price=0)
        booking_musique_physical1 = create_booking(user_booking, stock_musique_physical)
        booking_musique_physical2 = create_booking(user_booking, stock_musique_physical, quantity=2)
        booking_musique_digital = create_booking(user_booking, stock_musique_digital)
        PcObject.save(stock_cinema1, stock_cinema2, booking_musique_physical1, booking_musique_physical2,
                      booking_musique_digital)

        # When
        booking_counts = _query_get_booking_counts_grouped_by_type_and_medium().fetchall()

        # Then
        assert booking_counts == []


class CountAllCancelledBookingsTest:
    @clean_database
    def test_returns_2_when_not_filtered(self, app):
        # Given
        user_in_76 = create_user(departement_code='76', email='user-76@example.net')
        user_in_41 = create_user(departement_code='41', email='user-41@example.net')

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)

        booking1 = create_booking(user_in_76, stock, is_cancelled=True)
        booking2 = create_booking(user_in_41, stock, is_cancelled=True)
        booking3 = create_booking(user_in_41, stock, is_cancelled=False)
        PcObject.save(booking1, booking2, booking3)

        # When
        number_of_bookings = count_all_cancelled_bookings()

        # Then
        assert number_of_bookings == 2

    @clean_database
    def test_returns_1_when_filtered_on_user_departement(self, app):
        # Given
        user_in_76 = create_user(departement_code='76', email='user-76@example.net')
        user_in_41 = create_user(departement_code='41', email='user-41@example.net')

        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer, price=0)

        booking1 = create_booking(user_in_76, stock, is_cancelled=True)
        booking2 = create_booking(user_in_41, stock, is_cancelled=True)
        booking3 = create_booking(user_in_41, stock, is_cancelled=False)
        PcObject.save(booking1, booking2, booking3)

        # When
        number_of_bookings = count_all_cancelled_bookings('41')

        # Then
        assert number_of_bookings == 1
