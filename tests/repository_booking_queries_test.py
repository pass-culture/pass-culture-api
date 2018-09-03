from datetime import datetime, timedelta

import pytest

from models import PcObject
from repository.booking_queries import find_all_by_offerer_sorted_by_date_modified_asc
from tests.conftest import clean_database
from utils.test_utils import create_offerer, create_venue, create_stock_with_thing_offer, create_booking, create_user, \
    create_deposit, create_stock_with_event_offer


@clean_database
@pytest.mark.standalone
def test_find_all_by_offerer_sorted_by_date_modified_asc_with_event_and_things(app):
    # given
    user = create_user()
    now = datetime.utcnow()
    create_deposit(user, now, amount=1600)
    offerer1 = create_offerer(siren='123456789')
    offerer2 = create_offerer(siren='987654321')
    venue1 = create_venue(offerer1)
    venue2 = create_venue(offerer2)
    stock1 = create_stock_with_event_offer(offerer1, venue1, price=200)
    stock2 = create_stock_with_thing_offer(offerer1, venue1, thing_offer=None, price=300)
    stock3 = create_stock_with_thing_offer(offerer2, venue2, thing_offer=None, price=400)
    booking1 = create_booking(user, stock1, venue1, recommendation=None, quantity=2,
                              date_modified=now - timedelta(days=5))
    booking2 = create_booking(user, stock2, venue1, recommendation=None, quantity=1,
                              date_modified=now - timedelta(days=10))
    booking3 = create_booking(user, stock3, venue2, recommendation=None, quantity=2,
                              date_modified=now - timedelta(days=1))

    PcObject.check_and_save(booking1, booking2, booking3)

    # when
    bookings = find_all_by_offerer_sorted_by_date_modified_asc(offerer1.id)

    # then
    assert bookings[0].dateModified < bookings[1].dateModified
    assert booking1 in bookings
    assert booking2 in bookings
    assert booking3 not in bookings
