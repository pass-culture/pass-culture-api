from datetime import datetime
from datetime import timedelta
from unittest.mock import patch

import pytest
from pytest import approx

from pcapi.model_creators.generic_creators import create_booking
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_stock
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_offer_with_event_product
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.model_creators.specific_creators import create_stock_from_offer
from pcapi.model_creators.specific_creators import create_stock_with_event_offer
from pcapi.model_creators.specific_creators import create_stock_with_thing_offer
from pcapi.models import ApiErrors
from pcapi.models import Stock
from pcapi.models.pc_object import DeletedRecordException
from pcapi.repository import repository


EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST = timedelta(hours=72)


@pytest.mark.usefixtures("db_session")
def test_date_modified_should_be_updated_if_quantity_changed(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock(date_modified=datetime(2018, 2, 12), offer=offer, quantity=1)
    repository.save(stock)

    # when
    stock = Stock.query.first()
    stock.quantity = 10
    repository.save(stock)

    # then
    stock = Stock.query.first()
    assert stock.dateModified.timestamp() == approx(datetime.now().timestamp())


@pytest.mark.usefixtures("db_session")
def test_date_modified_should_not_be_updated_if_price_changed(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock(date_modified=datetime(2018, 2, 12), offer=offer, price=1, quantity=1)
    repository.save(stock)

    # when
    stock = Stock.query.first()
    stock.price = 5
    repository.save(stock)

    # then
    stock = Stock.query.first()
    assert stock.dateModified == datetime(2018, 2, 12)


@pytest.mark.usefixtures("db_session")
def test_queryNotSoftDeleted_should_not_return_soft_deleted(app):
    # Given
    offerer = create_offerer()
    venue = create_venue(offerer)
    stock = create_stock_with_event_offer(offerer, venue)
    stock.isSoftDeleted = True
    repository.save(stock)

    # When
    result = Stock.queryNotSoftDeleted().all()

    # Then
    assert not result


@pytest.mark.usefixtures("db_session")
def test_populate_dict_on_soft_deleted_object_raises_DeletedRecordException(app):
    # Given
    offerer = create_offerer()
    venue = create_venue(offerer)
    stock = create_stock_from_offer(create_offer_with_event_product(venue))
    stock.isSoftDeleted = True
    repository.save(stock)
    # When
    with pytest.raises(DeletedRecordException):
        stock.populate_from_dict({"quantity": 5})


@pytest.mark.usefixtures("db_session")
def test_stock_cannot_have_a_negative_price(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock_from_offer(offer, price=-10)

    # when
    with pytest.raises(ApiErrors) as e:
        repository.save(stock)

    # then
    assert e.value.errors["price"] is not None


@pytest.mark.usefixtures("db_session")
def test_stock_cannot_have_a_negative_quantity_stock(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock_from_offer(offer, quantity=-4)

    # when
    with pytest.raises(ApiErrors) as e:
        repository.save(stock)

    # then
    assert e.value.errors["quantity"] == ["Le stock doit être positif"]


@pytest.mark.usefixtures("db_session")
def test_stock_can_have_an_quantity_stock_equal_to_zero(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock_from_offer(offer, quantity=0)

    # when
    repository.save(stock)

    # then
    assert stock.quantity == 0


@pytest.mark.usefixtures("db_session")
def test_quantity_stocks_can_be_changed_even_when_bookings_with_cancellations_exceed_quantity(app):
    # Given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock_from_offer(offer, quantity=2, price=0)
    repository.save(stock)
    user1 = create_user()
    user2 = create_user(email="test@mail.com")

    cancelled_booking1 = create_booking(user=user1, stock=stock, is_cancelled=True, quantity=1)
    cancelled_booking2 = create_booking(user=user1, stock=stock, is_cancelled=True, quantity=1)
    booking1 = create_booking(user=user1, stock=stock, is_cancelled=False, quantity=1)
    booking2 = create_booking(user=user2, stock=stock, is_cancelled=False, quantity=1)

    repository.save(cancelled_booking1, cancelled_booking2, booking1, booking2)
    stock.quantity = 3

    # Then the following should not raise
    repository.save(stock)


@pytest.mark.usefixtures("db_session")
def test_should_update_stock_quantity_when_value_is_more_than_sum_of_bookings_quantity(app):
    # Given
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock_from_offer(offer, quantity=2, price=0)
    repository.save(stock)
    user = create_user()
    booking = create_booking(user=user, stock=stock, is_cancelled=False, quantity=2)
    repository.save(booking)
    stock.quantity = 3

    # When
    repository.save(stock)

    # Then
    assert Stock.query.get(stock.id).quantity == 3


@pytest.mark.usefixtures("db_session")
def test_should_not_update_quantity_stock_when_value_is_less_than_booking_count(app):
    # given
    user = create_user()
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_offer_with_thing_product(venue)
    stock = create_stock_from_offer(offer, price=0, quantity=10)
    booking = create_booking(user=user, stock=stock, quantity=5)
    repository.save(booking)
    stock.quantity = 4

    # when
    with pytest.raises(ApiErrors) as e:
        repository.save(stock)

    # then
    assert e.value.errors["quantity"] == ["Le stock total ne peut être inférieur au nombre de réservations"]


class IsBookableTest:
    def test_should_return_false_when_booking_limit_datetime_has_passed(self):
        # Given
        limit_datetime = datetime.utcnow() - timedelta(days=2)
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        # When
        stock = create_stock(booking_limit_datetime=limit_datetime, offer=offer)

        # Then
        assert not stock.isBookable

    def test_should_return_false_when_offerer_is_not_validated(self):
        # Given
        offerer = create_offerer(validation_token="validation_token")
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        # When
        stock = create_stock(offer=offer)

        # Then
        assert not stock.isBookable

    def test_should_return_false_when_offerer_is_not_active(self):
        # Given
        offerer = create_offerer(is_active=False)
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        # When
        stock = create_stock(offer=offer)

        # Then
        assert not stock.isBookable

    def test_should_return_false_when_venue_is_not_validated(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, validation_token="ZERTYUIO")
        offer = create_offer_with_thing_product(venue)

        # When
        stock = create_stock(offer=offer)

        # Then
        assert not stock.isBookable

    def test_should_return_false_when_offer_is_not_active(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue, is_active=False)

        # When
        stock = create_stock(offer=offer)

        # Then
        assert not stock.isBookable

    def test_should_return_false_when_stock_is_soft_deleted(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        # When
        stock = create_stock(is_soft_deleted=True, offer=offer)

        # Then
        assert not stock.isBookable

    def test_should_return_false_when_offer_is_event_with_passed_begining_datetime(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue)
        expired_stock_date = datetime.utcnow() - timedelta(days=2)

        # When
        stock = create_stock(beginning_datetime=expired_stock_date, offer=offer)

        # Then
        assert not stock.isBookable

    @pytest.mark.usefixtures("db_session")
    def test_should_return_false_when_no_remaining_stock(self, app):
        # Given
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue)

        # When
        stock = create_stock(offer=offer, price=0, quantity=10)
        booking = create_booking(user, stock=stock, quantity=10)
        repository.save(booking)

        # Then
        assert not stock.isBookable

    def test_should_return_true_when_stock_is_unlimited(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_event_product(venue)

        # When
        stock = create_stock(offer=offer, price=0, quantity=None)

        # Then
        assert stock.isBookable

    def test_should_return_true_when_stock_requirements_are_fulfilled(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer = create_offer_with_thing_product(venue)

        # When
        stock = create_stock(offer=offer)

        # Then
        assert stock.isBookable


class IsEventExpiredTest:
    def test_is_not_expired_when_stock_is_not_an_event(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        stock = create_stock_with_thing_offer(offerer=offerer, venue=venue)

        # When
        is_event_expired = stock.isEventExpired

        # Then
        assert is_event_expired is False

    def test_is_not_expired_when_stock_is_an_event_in_the_future(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        three_days_from_now = datetime.utcnow() + timedelta(hours=72)
        stock = create_stock_with_event_offer(offerer=offerer, venue=venue, beginning_datetime=three_days_from_now)

        # When
        is_event_expired = stock.isEventExpired

        # Then
        assert is_event_expired is False

    def test_is_expired_when_stock_is_an_event_in_the_past(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        one_day_in_the_past = datetime.utcnow() - timedelta(hours=24)
        stock = create_stock_with_event_offer(offerer=offerer, venue=venue, beginning_datetime=one_day_in_the_past)

        # When
        is_event_expired = stock.isEventExpired

        # Then
        assert is_event_expired is True


class IsEventDeletableTest:
    @patch("pcapi.core.offers.models.EVENT_AUTOMATIC_REFUND_DELAY", EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST)
    def test_is_deletable_when_stock_is_not_an_event(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        stock = create_stock_with_thing_offer(offerer=offerer, venue=venue)

        # When
        is_event_deletable = stock.isEventDeletable

        # Then
        assert is_event_deletable is True

    @patch("pcapi.core.offers.models.EVENT_AUTOMATIC_REFUND_DELAY", EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST)
    def test_is_deletable_when_stock_is_an_event_in_the_future(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        three_days_from_now = datetime.utcnow() + timedelta(hours=72)
        stock = create_stock_with_event_offer(offerer=offerer, venue=venue, beginning_datetime=three_days_from_now)

        # When
        is_event_deletable = stock.isEventDeletable

        # Then
        assert is_event_deletable is True

    @patch("pcapi.core.offers.models.EVENT_AUTOMATIC_REFUND_DELAY", EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST)
    def test_is_deletable_when_stock_is_expired_since_less_than_event_automatic_refund_delay(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        expired_date_but_not_automaticaly_refunded = (
            datetime.utcnow() - EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST + timedelta(1)
        )
        stock = create_stock_with_event_offer(
            offerer=offerer, venue=venue, beginning_datetime=expired_date_but_not_automaticaly_refunded
        )

        # When
        is_event_deletable = stock.isEventDeletable

        # Then
        assert is_event_deletable is True

    @patch("pcapi.core.offers.models.EVENT_AUTOMATIC_REFUND_DELAY", EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST)
    def test_is_not_deletable_when_stock_is_expired_since_more_than_event_automatic_refund_delay(self):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        expired_date_and_automaticaly_refunded = datetime.utcnow() - EVENT_AUTOMATIC_REFUND_DELAY_FOR_TEST
        stock = create_stock_with_event_offer(
            offerer=offerer, venue=venue, beginning_datetime=expired_date_and_automaticaly_refunded
        )

        # When
        is_event_deletable = stock.isEventDeletable

        # Then
        assert is_event_deletable is False
