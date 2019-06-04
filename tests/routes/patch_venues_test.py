from models import PcObject
from models.db import db
from tests.conftest import clean_database, TestClient
from tests.test_utils import API_URL, create_venue, create_offerer, create_user, create_user_offerer
from utils.human_ids import humanize


class Patch:
    class Returns200:
        @clean_database
        def when_patch_siret_when_there_is_none_yet(self, app):
            # Given
            offerer = create_offerer()
            user = create_user()
            user_offerer = create_user_offerer(user, offerer, is_admin=True)
            siret = offerer.siren + '11111'
            venue = create_venue(offerer, comment="Pas de siret", siret=None)
            PcObject.save(user_offerer, venue)
            venue_data = {
                'siret': siret,
            }

            auth_request = TestClient().with_auth(email=user.email)

            # when
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue.id), json=venue_data)

            # Then
            assert response.status_code == 200
            assert response.json()['siret'] == siret

        @clean_database
        def when_patch_siret_when_there_is_one_already_but_equal(self, app):
            # Given
            offerer = create_offerer()
            user = create_user()
            user_offerer = create_user_offerer(user, offerer, is_admin=True)
            siret = offerer.siren + '11111'
            venue = create_venue(offerer, siret=siret)
            PcObject.save(user_offerer, venue)
            venue_data = {
                'siret': siret,
            }
            auth_request = TestClient().with_auth(email=user.email)

            # when
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue.id), json=venue_data)

            # Then
            assert response.status_code == 200
            assert response.json()['siret'] == siret

        @clean_database
        def when_user_has_rights_on_managing_offerer(self, app):
            # given
            offerer = create_offerer()
            user = create_user(email='user.pro@test.com')
            venue = create_venue(offerer, name='L\'encre et la plume')
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user_offerer, venue)
            auth_request = TestClient().with_auth(email=user.email)

            # when
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue.id), json={'name': 'Ma librairie'})

            # then
            assert response.status_code == 200
            db.session.refresh(venue)
            assert venue.name == 'Ma librairie'
            json = response.json()
            assert json['isValidated'] == True
            assert 'validationToken' not in json
            assert venue.isValidated

    class Returns400:
        @clean_database
        def when_trying_to_patch_siret_when_already_one(self, app):
            # Given
            offerer = create_offerer()
            user = create_user()
            user_offerer = create_user_offerer(user, offerer, is_admin=True)
            siret = offerer.siren + '11111'
            venue = create_venue(offerer, siret=siret)
            PcObject.save(user_offerer, venue)
            venue_data = {
                'siret': offerer.siren + '12345',
            }
            auth_request = TestClient().with_auth(email=user.email)

            # when
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue.id), json=venue_data)

            # Then
            assert response.status_code == 400
            assert response.json()['siret'] == ['Vous ne pouvez pas modifier le siret d\'un lieu']

        @clean_database
        def when_editing_is_virtual_and_managing_offerer_already_has_virtual_venue(self, app):
            # given
            offerer = create_offerer()
            user = create_user(email='user.pro@test.com')
            venue1 = create_venue(offerer, name='Les petits papiers', is_virtual=True, siret=None)
            venue2 = create_venue(offerer, name='L\'encre et la plume', is_virtual=False)
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user_offerer, venue1, venue2)
            auth_request = TestClient().with_auth(email=user.email)

            # when
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue2.id), json={'isVirtual': True})

            # then
            assert response.status_code == 400
            assert response.json() == {
                'isVirtual': ['Un lieu pour les offres numériques existe déjà pour cette structure']}

        @clean_database
        def when_latitude_out_of_range_and_longitude_wrong_format(self, app):
            # given
            offerer = create_offerer()
            user = create_user(email='user.pro@test.com')
            venue = create_venue(offerer, name='Les petits papiers', is_virtual=False)
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user_offerer, venue)
            auth_request = TestClient().with_auth(email=user.email)
            data = {'latitude': -98.82387, 'longitude': '112°3534'}

            # when
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue.id), json=data)

            # then
            assert response.status_code == 400
            assert response.json()['latitude'] == ['La latitude doit être comprise entre -90.0 et +90.0']
            assert response.json()['longitude'] == ['Format incorrect']

        @clean_database
        def when_trying_to_edit_managing_offerer(self, app):
            # Given
            offerer = create_offerer(siren='123456789')
            other_offerer = create_offerer(siren='987654321')
            user = create_user(email='user.pro@test.com')
            venue = create_venue(offerer, name='Les petits papiers', is_virtual=False)
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user_offerer, venue, other_offerer)
            auth_request = TestClient().with_auth(email=user.email)

            # When
            response = auth_request.patch(API_URL + '/venues/%s' % humanize(venue.id),
                                          json={'managingOffererId': humanize(other_offerer.id)})

            # Then
            assert response.status_code == 400
            assert response.json()['managingOffererId'] == ['Vous ne pouvez pas changer la structure d\'un lieu']
