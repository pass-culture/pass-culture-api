""" routes event occurrences tests """
import pytest

from models.db import db
from models.pc_object import PcObject
from tests.conftest import clean_database
from utils.human_ids import humanize
from utils.test_utils import API_URL,\
                             create_booking, \
                             create_event_occurrence, \
                             create_event_offer, \
                             create_offerer, \
                             create_recommendation, \
                             create_stock_from_event_occurrence, \
                             create_user_offerer, \
                             create_user, \
                             create_venue, \
                             req_with_auth



@clean_database
@pytest.mark.standalone
def test_10_get_event_occurences_should_return_a_list_of_event_occurences(app):
    # Given
    user = create_user(email='test@email.com', password='P@55w0rd', is_admin=True, can_book_free_offers=False)
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer = create_event_offer(venue)
    eo1 = create_event_occurrence(offer)
    eo2 = create_event_occurrence(offer)
    eo3 = create_event_occurrence(offer)

    PcObject.check_and_save(user, eo1, eo2, eo3)

    # When
    request = req_with_auth('test@email.com', 'P@55w0rd').get(API_URL + '/eventOccurrences')

    # Then
    assert request.status_code == 200
    eos = request.json()
    assert len(eos) == 3

@clean_database
@pytest.mark.standalone
def test_when_deleted_event_occurrence_only_all_bookings_related_to_soft_deleted_event_occurence_are_cancelled(app):
    # Given
    user1 = create_user(email='user1@test.fr')
    user2 = create_user(email='user2@test.fr')
    user_admin = create_user(email='email@test.fr', password='P@55w0rd')
    offerer = create_offerer()
    user_offerer = create_user_offerer(user_admin, offerer)
    venue = create_venue(offerer)
    offer = create_event_offer(venue)
    event_occurrence1 = create_event_occurrence(offer)
    event_occurrence2 = create_event_occurrence(offer)
    stock1 = create_stock_from_event_occurrence(offerer, event_occurrence1, price=0, available=10)
    stock2 = create_stock_from_event_occurrence(offerer, event_occurrence2, price=0, available=10)
    recommendation1 = create_recommendation(offer, user1)
    recommendation2 = create_recommendation(offer, user2)
    booking1 = create_booking(user1, stock1, venue, recommendation=recommendation1, fill_stock_bookings=False)
    booking2 = create_booking(user1, stock2, venue, recommendation=recommendation1, fill_stock_bookings=False)
    booking3 = create_booking(user2, stock1, venue, recommendation=recommendation2, fill_stock_bookings=False)

    PcObject.check_and_save(event_occurrence, booking1, booking2, booking3, user_offerer)

    # When
    req_with_auth('email@test.fr', 'P@55w0rd').delete(API_URL + '/eventOccurrences/' + humanize(event_occurrence1.id))

    # Then
    db.session.refresh(booking1)
    db.session.refresh(booking2)
    db.session.refresh(booking3)
    assert booking1.isCancelled == True
    assert booking2.isCancelled == False
    assert booking3.isCancelled == True
