from unittest.mock import patch

from routes.serialization.recommendation_serialize import serialize_recommendation, serialize_recommendations
from tests.test_utils import create_recommendation, create_user, create_offerer, create_venue, \
    create_mediation, create_booking, create_stock, \
    create_offer_with_thing_product, create_product_with_thing_type


class SerializeRecommendationTest:
    @patch('routes.serialization.recommendation_serialize.booking_queries.find_from_recommendation')
    def test_should_return_booking_if_query_booking_is_True(self, find_from_recommendation):
        # Given
        user = create_user(email='user@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        product = create_product_with_thing_type(dominant_color=b'\x00\x00\x00', thumb_count=1)
        offer = create_offer_with_thing_product(product=product, venue=venue)
        stock = create_stock(offer=offer)
        mediation = create_mediation(offer)
        recommendation = create_recommendation(offer, user, mediation=mediation)
        find_from_recommendation.return_value = [create_booking(user, stock, venue, recommendation)]

        # When
        serialized_recommendation = serialize_recommendation(recommendation, user, query_booking=True)

        # Then
        assert 'bookings' in serialized_recommendation
        assert serialized_recommendation['bookings'] is not None

    @patch('routes.serialization.recommendation_serialize.booking_queries.find_from_recommendation')
    def test_should_not_return_booking_if_query_booking_is_False(self, find_from_recommendation):
        # Given
        user = create_user(email='user@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        product = create_product_with_thing_type(dominant_color=b'\x00\x00\x00', thumb_count=1)
        offer = create_offer_with_thing_product(product=product, venue=venue)
        stock = create_stock(offer=offer)
        mediation = create_mediation(offer)
        recommendation = create_recommendation(offer, user, mediation=mediation)
        find_from_recommendation.return_value = [create_booking(user, stock, venue, recommendation)]

        # When
        serialized_recommendation = serialize_recommendation(recommendation, user, query_booking=False)

        # Then
        assert 'bookings' not in serialized_recommendation

    @patch('routes.serialization.recommendation_serialize.booking_queries.find_from_recommendation')
    def test_should_not_return_booking_if_recommendation_does_not_have_offer(self, find_from_recommendation):
        # Given
        user = create_user(email='user@test.com')
        mediation = create_mediation(tuto_index=1)
        recommendation = create_recommendation(user=user, mediation=mediation)
        recommendation.mediationId = 1
        find_from_recommendation.return_value = []

        # When
        serialized_recommendation = serialize_recommendation(recommendation, user, query_booking=True)

        # Then
        assert 'bookings' not in serialized_recommendation


class SerializeRecommendationsTest:
    @patch('routes.serialization.recommendation_serialize.booking_queries.find_from_recommendation')
    @patch('routes.serialization.recommendation_serialize.booking_queries.find_for_my_bookings_page')
    def test_should_call_find_for_my_bookings_page_and_not_find_from_recommendation(self, find_for_my_bookings_page, find_from_recommendation):
        # Given
        user = create_user(email='user@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        product = create_product_with_thing_type(dominant_color=b'\x00\x00\x00', thumb_count=1)
        offer = create_offer_with_thing_product(product=product, venue=venue)
        stock = create_stock(offer=offer)
        stock.offerId = 1
        mediation = create_mediation(offer)
        recommendation = create_recommendation(offer, user, mediation=mediation)
        recommendation.offerId = 1
        find_for_my_bookings_page.return_value = [create_booking(user, stock, venue, recommendation)]

        # When
        serialized_recommendations = serialize_recommendations([recommendation], user)

        # Then
        find_for_my_bookings_page.assert_called_once()
        find_from_recommendation.assert_not_called()
        assert 'bookings' in serialized_recommendations[0]

    @patch('routes.serialization.recommendation_serialize.booking_queries.find_for_my_bookings_page')
    def test_should_return_dict_with_bookings_key_and_empty_list_when_no_bookings(self, find_for_my_bookings_page):
        # Given
        user = create_user(email='user@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        product = create_product_with_thing_type(dominant_color=b'\x00\x00\x00', thumb_count=1)
        offer = create_offer_with_thing_product(product=product, venue=venue)
        stock = create_stock(offer=offer)
        stock.offerId = 1
        mediation = create_mediation(offer)
        recommendation = create_recommendation(offer, user, mediation=mediation)
        recommendation.offerId = 1
        find_for_my_bookings_page.return_value = []

        # When
        serialized_recommendations = serialize_recommendations([recommendation], user)

        # Then
        assert serialized_recommendations[0]['bookings'] == []

    @patch('routes.serialization.recommendation_serialize.booking_queries.find_for_my_bookings_page')
    def test_should_return_dict_with_bookings_key_and_empty_list_for_recommendation_without_bookings_and_with_serialized_booking_list_for_recommendation_with_booking(self, find_for_my_bookings_page):
        # Given
        user = create_user(email='user@test.com')
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue)
        offer2 = create_offer_with_thing_product(venue)
        stock1 = create_stock(offer=offer1)
        stock2 = create_stock(offer=offer2)
        stock1.offerId = 1
        stock2.offerId = 2
        mediation1 = create_mediation(offer1)
        mediation2 = create_mediation(offer2)
        recommendation1 = create_recommendation(offer1, user, mediation=mediation1)
        recommendation1.offerId = 1
        recommendation2 = create_recommendation(offer2, user, mediation=mediation2)
        recommendation2.offerId = 2
        find_for_my_bookings_page.return_value = [create_booking(user, stock2, venue, recommendation2)]

        # When
        serialized_recommendations = serialize_recommendations([recommendation1, recommendation2], user)

        # Then
        assert serialized_recommendations[0]['bookings'] == []
        assert serialized_recommendations[1]['bookings'] != []
