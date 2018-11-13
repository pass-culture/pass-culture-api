import pytest

from models import PcObject
from tests.conftest import clean_database
from utils.human_ids import humanize
from utils.test_utils import req_with_auth, create_user, API_URL, create_venue, create_offerer, create_thing


@clean_database
@pytest.mark.standalone
def test_things_with_urls_cannot_be_saved_with_type_offline_only(app):
    # Given
    user = create_user(password='P@55W0rd!')
    offerer = create_offerer()
    venue = create_venue(offerer, is_virtual=True, siret=None)
    PcObject.check_and_save(user, venue)
    thing_json = {'thumbCount': 0, 'type': 'ThingType.JEUX_ABO', 'name': 'Le grand jeu',
                  'mediaUrls': 'http://media.url',
                  'url': 'http://jeux_abo.fr/offre', 'isNational': False, 'venueId': humanize(venue.id)}

    # When
    response = req_with_auth(email=user.email, password='P@55W0rd!').post(API_URL + '/things', json=thing_json)

    # Then
    assert response.status_code == 400
    assert response.json()['url'] == ['Une offre de type Jeux (Abonnements) ne peut pas être numérique']


@clean_database
@pytest.mark.standalone
def test_things_with_invalid_urls_cannot_be_saved(app):
    # Given
    user = create_user(password='P@55W0rd!')
    offerer = create_offerer()
    venue = create_venue(offerer, is_virtual=True, siret=None)
    PcObject.check_and_save(user, venue)
    thing_json = {'thumbCount': 0, 'type': 'ThingType.JEUX_ABO', 'name': 'Le grand jeu',
                  'mediaUrls': 'http://media.url',
                  'url': 'ftp://invalid.url', 'isNational': False, 'venueId': humanize(venue.id)}

    # When
    response = req_with_auth(email=user.email, password='P@55W0rd!').post(API_URL + '/things', json=thing_json)

    # Then
    assert response.status_code == 400
    assert response.json()['url'] == ["L'URL doit commencer par \"http://\" ou \"https://\""]


@clean_database
@pytest.mark.standalone
def test_things_with_urls_must_have_virtual_venue(app):
    # Given
    user = create_user(password='P@55W0rd!')
    offerer = create_offerer()
    venue = create_venue(offerer, is_virtual=False)
    PcObject.check_and_save(user, venue)
    thing_json = {'thumbCount': 0, 'type': 'ThingType.JEUX_VIDEO', 'name': 'Les lapins crétins',
                  'mediaUrls': 'http://media.url',
                  'url': 'http://jeux.fr/offre', 'isNational': False, 'venueId': humanize(venue.id)}

    # When
    response = req_with_auth(email=user.email, password='P@55W0rd!').post(API_URL + '/things', json=thing_json)

    # Then
    assert response.status_code == 400
    assert response.json()['venue'] == [
        'Une offre numérique doit obligatoirement être associée au lieu "Offre en ligne"']


@clean_database
@pytest.mark.standalone
def test_things_with_invalid_urls_cannot_be_modified(app):
    # Given
    user = create_user(password='P@55W0rd!')
    offerer = create_offerer()
    venue = create_venue(offerer, is_virtual=True, siret=None)
    thing = create_thing()
    PcObject.check_and_save(user, venue, thing)
    thing_json = {'url': 'ftp://invalid.url'}
    auth_request = req_with_auth(email=user.email, password='P@55W0rd!')

    # When
    response = auth_request.patch(API_URL + '/things/%s' % humanize(thing.id), json=thing_json)

    # Then
    assert response.status_code == 400
    assert response.json()['url'] == ["L'URL doit commencer par \"http://\" ou \"https://\""]
