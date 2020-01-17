from datetime import datetime, timedelta
from unittest.mock import Mock

from algolia.rules_engine import is_eligible_for_indexing
from models import PcObject
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_offerer, create_stock, create_venue
from tests.model_creators.specific_creators import create_offer_with_thing_product

YESTERDAY = datetime.now() - timedelta(days=1)
TOMORROW = datetime.now() + timedelta(days=1)


class IsEligibleForIndexingTest:
    @clean_database
    def test_should_return_false_when_none_is_given(self, app):
        # Given
        offerer = create_offerer(is_active=True, validation_token=None)
        venue = create_venue(offerer=offerer, validation_token=None)
        offer = create_offer_with_thing_product(venue=venue, is_active=True)
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=None, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(None)

        # Then
        assert is_eligible is False

    @clean_database
    def test_should_return_false_when_offerer_is_not_active(self, app):
        # Given
        offerer = create_offerer(is_active=False, validation_token=None)
        venue = create_venue(offerer=offerer, validation_token=None)
        offer = create_offer_with_thing_product(venue=venue, is_active=True)
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=None, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(offer)

        # Then
        assert is_eligible is False

    @clean_database
    def test_should_return_false_when_offerer_is_active_but_is_not_validated(self, app):
        # Given
        offerer = create_offerer(is_active=True, validation_token='FAKE_TOKEN')
        venue = create_venue(offerer=offerer, validation_token=None)
        offer = create_offer_with_thing_product(venue=venue, is_active=True)
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=None, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(offer)

        # Then
        assert is_eligible is False

    @clean_database
    def test_should_return_false_when_offer_is_not_active(self, app):
        # Given
        offerer = create_offerer(is_active=True, validation_token=None)
        venue = create_venue(offerer=offerer, validation_token=None)
        offer = create_offer_with_thing_product(venue=venue, is_active=False)
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=None, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(offer)

        # Then
        assert is_eligible is False

    @clean_database
    def test_should_return_false_when_offer_has_not_enough_stock(self, app):
        # Given
        offerer = create_offerer(is_active=True, validation_token=None)
        venue = create_venue(offerer=offerer, validation_token=None)
        offer = create_offer_with_thing_product(venue=venue, is_active=True)
        offer.has_enough_stock_to_be_booked = Mock()
        offer.has_enough_stock_to_be_booked.return_value = False
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=1, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(offer)

        # Then
        assert is_eligible is False

    @clean_database
    def test_should_return_false_when_venue_is_not_validated(self, app):
        # Given
        offerer = create_offerer(is_active=True, validation_token=None)
        venue = create_venue(offerer=offerer, validation_token='FAKE_TOKEN')
        offer = create_offer_with_thing_product(venue=venue, is_active=True)
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=None, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(offer)

        # Then
        assert is_eligible is False

    @clean_database
    def test_should_return_true_when_offer_is_eligible(self, app):
        # Given
        offerer = create_offerer(is_active=True, validation_token=None)
        venue = create_venue(offerer=offerer, validation_token=None)
        offer = create_offer_with_thing_product(venue=venue, is_active=True)
        stock = create_stock(offer=offer, booking_limit_datetime=TOMORROW, available=1, is_soft_deleted=False)
        PcObject.save(stock)

        # When
        is_eligible = is_eligible_for_indexing(offer)

        # Then
        assert is_eligible is True
