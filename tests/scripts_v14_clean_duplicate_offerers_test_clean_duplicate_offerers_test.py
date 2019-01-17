from unittest.mock import patch, Mock

import pandas as pd
import pytest

from models import PcObject, Offerer, Venue, UserOfferer, Offer
from scripts.v14_clean_duplicate_offerers.clean_duplicate_offerers import correct_venue_id, delete_offerers_KO, correct_mananging_offerer_id, \
    delete_venues_linked_to_offerers_KO, delete_user_offerers_linked_to_offerers_KO, clean_offerers_KO
from tests.conftest import clean_database
from utils.test_utils import create_offerer, create_venue, create_thing_offer, create_user_offerer, create_user


@clean_database
@pytest.mark.standalone
def test_correct_venue_id_should_change_venue_id_from_offers_whose_venue_id_appear_in_venue_KO_id(app):
    # Given
    offerer_KO = create_offerer(siren='123456789')
    offerer_OK = create_offerer(siren='987654321')
    venue_KO = create_venue(offerer_KO, siret=offerer_KO.siren + '12345')
    venue_OK = create_venue(offerer_OK, siret=offerer_OK.siren + '12345')
    offer_KO = create_thing_offer(venue_KO)
    PcObject.check_and_save(offerer_KO, offerer_OK, venue_KO, venue_OK, offer_KO)
    dataframe = pd.DataFrame(
        columns=['offerer_KO_id', 'offerer_KO_name', 'offerer_OK_id', 'offerer_OK_name', 'venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name'],
        data=[[offerer_KO.id, offerer_KO.name, offerer_OK.id, offerer_OK.name, venue_KO.id, venue_KO.name, venue_OK.id, venue_OK.name]]
    )

    # When
    correct_venue_id(dataframe)

    # then
    assert offer_KO.venueId == venue_OK.id


@clean_database
@pytest.mark.standalone
def test_correct_mananging_offerer_id_should_change_offerer_id_from_venues_whose_id_appear_in_venue_KO_id(app):
    # Given
    offerer_KO = create_offerer(siren='123456789')
    offerer_OK = create_offerer(siren='987654321')
    venue_KO = create_venue(offerer_KO, siret=None, comment='test')
    PcObject.check_and_save(offerer_KO, offerer_OK, venue_KO)
    dataframe = pd.DataFrame(
        columns=['offerer_KO_id', 'offerer_KO_name', 'offerer_OK_id', 'offerer_OK_name', 'venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name'],
        data=[[offerer_KO.id, offerer_KO.name, offerer_OK.id, offerer_OK.name, venue_KO.id, venue_KO.name, None, None]]
    )

    # When
    correct_mananging_offerer_id(dataframe)

    # then
    assert venue_KO.managingOffererId == offerer_OK.id


@clean_database
@pytest.mark.standalone
def test_delete_offerers_KO_should_delete_offerers_whose_id_appear_in_offerer_KO_id(app):
    # Given
    offerer_KO = create_offerer(siren='123456789')
    PcObject.check_and_save(offerer_KO)
    dataframe = pd.DataFrame(
        columns=['offerer_KO_id', 'offerer_OK_id', 'venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name'],
        data=[[offerer_KO.id, 1, 1, 'Test', None, None]]
    )

    # When
    delete_offerers_KO(dataframe)

    # then
    assert not Offerer.query.filter_by(id=offerer_KO.id).all()


@clean_database
@pytest.mark.standalone
def test_delete_venues_linked_to_offerers_KO_should_delete_venues_whose_managing_offerer_id_appear_in_offerer_KO_id(app):
    # Given
    offerer_KO = create_offerer(siren='123456789')
    venue_KO = create_venue(offerer_KO, siret=None, comment='test')
    PcObject.check_and_save(venue_KO)
    venue_ko_id = venue_KO.id
    assert Venue.query.filter_by(id=venue_ko_id).all()
    dataframe = pd.DataFrame(
        columns=['offerer_KO_id', 'offerer_OK_id', 'venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name'],
        data=[[offerer_KO.id, 1, venue_ko_id, venue_KO.name, None, None]]
    )

    # When
    delete_venues_linked_to_offerers_KO(dataframe)

    # then
    assert not Venue.query.filter_by(id=venue_ko_id).all()


@clean_database
@pytest.mark.standalone
def test_delete_user_offerers_linked_to_offerers_KO_should_delete_user_offerers_whose_fferer_id_appear_in_offerer_KO_id(app):
    # Given
    offerer_KO = create_offerer(siren='123456789')
    user_offerer = create_user_offerer(create_user(), offerer_KO)
    PcObject.check_and_save(user_offerer)
    dataframe = pd.DataFrame(
        columns=['offerer_KO_id', 'offerer_OK_id', 'venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name'],
        data=[[offerer_KO.id, 1, 1, 'Test', None, None]]
    )

    # When
    delete_user_offerers_linked_to_offerers_KO(dataframe)

    # then
    assert not UserOfferer.query.filter_by(offererId=offerer_KO.id).all()


@clean_database
@pytest.mark.standalone
def test_clean_offerers_KO_should_treat_db_dependencies_and_delete_all_objects_related_to_offerers_KO(app):
    # Given
    offerer_KO = create_offerer(siren='123456789')
    offerer_OK = create_offerer(siren='987654321')
    user_offerer = create_user_offerer(create_user(), offerer_KO)
    venue_KO_matched = create_venue(offerer_KO)
    offer_KO_matched = create_thing_offer(venue_KO_matched)
    venue_OK_matched = create_venue(offerer_OK, siret=offerer_OK.siren + '12345')
    venue_KO_not_matched = create_venue(offerer_KO, siret=None, comment='Test')
    PcObject.check_and_save(user_offerer, venue_KO_matched, venue_OK_matched, offer_KO_matched)
    offerer_ko_id = offerer_KO.id
    offerer_ok_id = offerer_OK.id
    venue_ok_matched_id = venue_OK_matched.id
    venue_ko_matched_id = venue_KO_matched.id
    dataframe = pd.DataFrame(
        columns=['offerer_KO_id', 'offerer_OK_id', 'venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name'],
        data=[[offerer_ko_id, offerer_ok_id, venue_ko_matched_id, venue_KO_matched.name, venue_ok_matched_id, venue_OK_matched.name],
              [offerer_ko_id, offerer_ok_id, venue_KO_not_matched.id, venue_KO_not_matched.name, None, None]]
    )
    get_venues_by_offerer_equivalences = Mock()
    get_venues_by_offerer_equivalences.return_value = dataframe

    # When
    with patch('scripts.v14_clean_duplicate_offerers.clean_duplicate_offerers.get_venue_equivalence', return_value=dataframe):
        clean_offerers_KO()

    # then
    assert not UserOfferer.query.filter_by(offererId=offerer_ko_id).all()
    assert not Venue.query.filter_by(managingOffererId=offerer_ko_id).all()
    assert len(Venue.query.filter_by(managingOffererId=offerer_ok_id).all()) == 2
    assert len(Offer.query.filter_by(venueId=venue_ok_matched_id).all()) == 1
    assert not Offer.query.filter_by(venueId=venue_ko_matched_id).all()
