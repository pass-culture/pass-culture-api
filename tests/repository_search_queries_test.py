import pytest

from models import PcObject, Event, Thing, Offer, Venue
from repository.search_queries import get_keywords_filter
from tests.conftest import clean_database
from utils.test_utils import create_event, create_thing, create_offerer, create_venue, create_event_offer, \
    create_thing_offer


@pytest.mark.standalone
@clean_database
def test_get_keywords_filter_returns_all_offers_with_event_or_thing_containing_keywords(app):
    # given
    event1 = create_event(event_name='Rencontre avec Jacques Martin')
    event2 = create_event(event_name='Concert de contrebasse')
    thing = create_thing(thing_name='Rencontre avec Belle du Seigneur')
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer1 = create_event_offer(venue, event1)
    offer2 = create_event_offer(venue, event2)
    offer3 = create_thing_offer(venue, thing)
    PcObject.check_and_save(offer1, offer2, offer3)
    models = [Event, Thing]

    # when
    search_filter = get_keywords_filter(models, 'Rencontre')

    # then
    found_offers = Offer.query.outerjoin(Event).outerjoin(Thing).filter(
        search_filter).all()
    assert len(found_offers) == 2
    found_offers_id = list(map(lambda x: x.id, found_offers))
    assert offer1.id in found_offers_id
    assert offer3.id in found_offers_id


@pytest.mark.standalone
@clean_database
def test_get_keywords_filter_returns_all_offers_with_event_or_thing_or_venue_containing_keywords(app):
    # given
    event1 = create_event(event_name='Rencontre avec Jacques Martin')
    event2 = create_event(event_name='Concert de contrebasse')
    thing = create_thing(thing_name='Belle du Seigneur')
    offerer = create_offerer()
    venue1 = create_venue(offerer, name='Bataclan', city='Paris', siret=offerer.siren + '12345')
    venue2 = create_venue(offerer, name='Librairie la Rencontre', city='Saint Denis', siret=offerer.siren + '54321')
    offer1 = create_event_offer(venue1, event1)
    offer2 = create_event_offer(venue1, event2)
    offer3 = create_thing_offer(venue2, thing)
    PcObject.check_and_save(offer1, offer2, offer3)
    models = [Event, Thing, Venue]

    # when
    search_filter = get_keywords_filter(models, 'Rencontre')

    # then
    found_offers = Offer.query.outerjoin(Event).outerjoin(Thing).join(Venue).filter(
        search_filter).all()
    assert len(found_offers) == 2
    found_offers_id = list(map(lambda x: x.id, found_offers))
    assert offer1.id in found_offers_id
    assert offer3.id in found_offers_id


@pytest.mark.standalone
@clean_database
@pytest.mark.skip
def test_get_keywords_filter_with_an_returns_all_offers_having_rencontre_and_bataclan_or_paris_in_event_thing_or_venue(app):
    # given
    event1 = create_event(event_name='Rencontre avec Jacques Martin')
    event2 = create_event(event_name='Concert de contrebasse')
    thing = create_thing(thing_name='Rencontre avec Belle du Seigneur')
    offerer = create_offerer()
    venue1 = create_venue(offerer, name='Bataclan', city='Paris', siret=offerer.siren + '12345')
    venue2 = create_venue(offerer, name='Stade de France', city='Saint Denis', siret=offerer.siren + '54321')
    offer1 = create_event_offer(venue1, event1)
    offer2 = create_event_offer(venue1, event2)
    offer3 = create_thing_offer(venue2, thing)
    PcObject.check_and_save(offer1, offer2, offer3)
    models = [Event, Thing, Venue]

    # when
    search_filter = get_keywords_filter(models, 'Rencontre _and_ Bataclan Paris')

    # then
    found_offers = Offer.query.outerjoin(Event).outerjoin(Thing).join(Venue).filter(search_filter).all()
    assert len(found_offers) == 1
    assert found_offers[0].id == offer1.id


@pytest.mark.standalone
@clean_database
def test_get_keywords_filter_with_partial_search_returns_all_offers_with_event_or_thing_or_venue_containing_keywords(app):
    # given
    event1 = create_event(event_name='Rencontre avec Jacques Martin')
    event2 = create_event(event_name='Concert de contrebasse')
    thing = create_thing(thing_name='Belle du Seigneur')
    offerer = create_offerer()
    venue1 = create_venue(offerer, name='Bataclan', city='Paris', siret=offerer.siren + '12345')
    venue2 = create_venue(offerer, name='Librairie la Rencontre', city='Saint Denis', siret=offerer.siren + '54321')
    offer1 = create_event_offer(venue1, event1)
    offer2 = create_event_offer(venue1, event2)
    offer3 = create_thing_offer(venue2, thing)
    PcObject.check_and_save(offer1, offer2, offer3)
    models = [Event, Thing, Venue]

    # when
    search_filter = get_keywords_filter(models, 'Rencon')

    # then
    found_offers = Offer.query.outerjoin(Event).outerjoin(Thing).join(Venue).filter(
        search_filter).all()
    assert len(found_offers) == 2
    found_offers_id = list(map(lambda x: x.id, found_offers))
    assert offer1.id in found_offers_id
    assert offer3.id in found_offers_id


@pytest.mark.standalone
@clean_database
def test_get_keywords_filter_with_partial_search_returns_all_offers_with_event_or_thing_or_venue_containing_keywords(app):
    # given
    event1 = create_event(event_name='Rencontre avec Jacques Martin')
    event2 = create_event(event_name='Concert de contrebasse')
    thing = create_thing(thing_name='Belle du Seigneur')
    offerer = create_offerer()
    venue1 = create_venue(offerer, name='Bataclan', city='Paris', siret=offerer.siren + '12345')
    venue2 = create_venue(offerer, name='Librairie la Rencontre', city='Saint Denis', siret=offerer.siren + '54321')
    offer1 = create_event_offer(venue1, event1)
    offer2 = create_event_offer(venue1, event2)
    offer3 = create_thing_offer(venue2, thing)
    PcObject.check_and_save(offer1, offer2, offer3)
    models = [Event, Thing, Venue]

    # when
    search_filter = get_keywords_filter(models, 'Rencontre avec Jac')

    # then
    found_offers = Offer.query.outerjoin(Event).outerjoin(Thing).join(Venue).filter(
        search_filter).all()
    assert len(found_offers) == 2
    found_offers_id = list(map(lambda x: x.id, found_offers))
    assert offer1.id in found_offers_id
    assert offer3.id in found_offers_id
