from models import PcObject, EventType, Offer, ThingType, Product, Offerer
from tests.conftest import clean_database, TestClient
from tests.test_utils import create_user, API_URL, create_offerer, create_venue, create_user_offerer, \
    create_product_with_Thing_type, \
    create_product_with_Event_type
from utils.human_ids import humanize, dehumanize


class Post:
    class Returns400:
        @clean_database
        def when_venue_id_is_not_received(self, app):
            # Given
            user = create_user(email='test@email.com')
            json = {
                'bookingEmail': 'offer@email.com',
                'name': 'La pièce de théâtre',
                'durationMinutes': 60,
                'type': str(ThingType.AUDIOVISUEL)
            }
            PcObject.save(user)

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 400
            assert request.json['venueId'] == ['Vous devez préciser un identifiant de lieu']

        @clean_database
        def when_no_duration_given_for_an_event(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user, user_offerer, venue)

            json = {
                'bookingEmail': 'offer@email.com',
                'name': 'Le concert de Mallory Knox',
                'type': str(EventType.SPECTACLE_VIVANT),
                'venueId': humanize(venue.id),
            }

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 201

        @clean_database
        def when_venue_is_not_found(self, app):
            # Given
            user = create_user(email='test@email.com')
            json = {
                'venueId': humanize(123),
                'name': 'La pièce de théâtre',
                'durationMinutes': 60
            }
            PcObject.save(user)

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 400
            assert request.json['global'] == [
                'Aucun objet ne correspond à cet identifiant dans notre base de données']

        @clean_database
        def when_new_offer_has_errors(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer, is_virtual=True, siret=None)
            PcObject.save(user, venue, user_offerer)
            json = {
                'type': 'ThingType.JEUX',
                'name': 'Le grand jeu',
                "url": 'http://legrandj.eu',
                'mediaUrls': ['http://media.url'],
                'venueId': humanize(venue.id)
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert response.status_code == 400
            assert response.json['url'] == ['Une offre de type Jeux (support physique) ne peut pas être numérique']

        @clean_database
        def when_offer_type_is_unknown(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer, is_virtual=False)
            event_product = create_product_with_Event_type()
            PcObject.save(user, venue, event_product, user_offerer)
            json = {
                'type': '',
                'name': 'Les lapins crétins',
                'mediaUrls': ['http://media.url'],
                'durationMinutes': 200,
                'venueId': humanize(venue.id),
                'bookingEmail': 'offer@email.com'
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert response.status_code == 400
            assert response.json['type'] == ['Le type de cette offre est inconnu']

    class Returns201:
        @clean_database
        def when_creating_a_new_event_offer(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user, user_offerer, venue)
            offerer_id = offerer.id

            json = {
                'venueId': humanize(venue.id),
                'bookingEmail': 'offer@email.com',
                'name': 'La pièce de théâtre',
                'durationMinutes': 60,
                'type': str(EventType.SPECTACLE_VIVANT)
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert response.status_code == 201
            assert response.json['product']['offerType'] == {
                'conditionalFields': ["author", "showType", "stageDirector", "performer"],
                'description': 'Suivre un géant de 12 mètres dans la ville ? '
                               'Rire aux éclats devant un stand up ? '
                               'Rêver le temps d’un opéra ou d’un spectacle de danse ? '
                               'Assister à une pièce de théâtre, '
                               'ou se laisser conter une histoire ?',
                'proLabel': 'Spectacle vivant',
                'appLabel': 'Spectacle vivant',
                'offlineOnly': True,
                'onlineOnly': False,
                'sublabel': 'Applaudir',
                'type': 'Event',
                'value': 'EventType.SPECTACLE_VIVANT'
            }
            assert response.json['isEvent'] is True
            assert response.json['isThing'] is False

            offer_id = dehumanize(response.json['id'])
            offer = Offer.query.filter_by(id=offer_id).first()
            assert offer.bookingEmail == 'offer@email.com'
            assert offer.venueId == venue.id
            event_id = dehumanize(response.json['product']['id'])
            event_product = Product.query.filter_by(id=event_id).first()
            assert event_product.durationMinutes == 60
            assert event_product.name == 'La pièce de théâtre'
            assert offer.type == str(EventType.SPECTACLE_VIVANT)
            assert offer.product.owningOfferer == Offerer.query.get(offerer_id)

        @clean_database
        def when_creating_a_new_event_offer_without_booking_email(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            user_offerer = create_user_offerer(user, offerer)
            PcObject.save(user, user_offerer, venue)

            json = {
                'venueId': humanize(venue.id),
                'name': 'La pièce de théâtre',
                'durationMinutes': 60,
                'type': str(EventType.SPECTACLE_VIVANT)
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            offer_id = dehumanize(response.json['id'])
            offer = Offer.query.filter_by(id=offer_id).first()
            assert response.status_code == 201
            assert offer.bookingEmail == None

        @clean_database
        def when_creating_new_thing_offer(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer, is_virtual=True, siret=None)
            thing_product = create_product_with_Thing_type()
            PcObject.save(user, venue, thing_product, user_offerer)
            offerer_id = offerer.id
            json = {
                'type': 'ThingType.JEUX_VIDEO',
                'name': 'Les lapins crétins',
                'mediaUrls': ['http://media.url'],
                'url': 'http://jeux.fr/offre',
                'venueId': humanize(venue.id),
                'bookingEmail': 'offer@email.com'
            }

            # When
            response = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert response.status_code == 201
            offer_id = dehumanize(response.json['id'])
            offer = Offer.query.filter_by(id=offer_id).first()
            assert offer.bookingEmail == 'offer@email.com'
            assert response.json['product']['offerType'] == {
                'conditionalFields': [],
                'description': 'Résoudre l’énigme d’un jeu de piste dans votre ville ? '
                               'Jouer en ligne entre amis ? '
                               'Découvrir cet univers étrange avec une manette ?',
                'proLabel': 'Jeux vidéo',
                'appLabel': 'Jeux vidéo',
                'offlineOnly': False,
                'onlineOnly': True,
                'sublabel': 'Jouer',
                'type': 'Thing',
                'value': 'ThingType.JEUX_VIDEO'
            }
            offer_id = dehumanize(response.json['id'])
            offer = Offer.query.filter_by(id=offer_id).first()
            assert offer.bookingEmail == 'offer@email.com'
            assert offer.venueId == venue.id
            thing_id = dehumanize(response.json['product']['id'])
            thing_product = Product.query.filter_by(id=thing_id).first()
            assert thing_product.name == 'Les lapins crétins'
            assert offer.type == str(ThingType.JEUX_VIDEO)
            assert thing_product.url == 'http://jeux.fr/offre'
            assert offer.url == 'http://jeux.fr/offre'
            assert offer.isDigital
            assert offer.isNational
            assert thing_product.isNational
            assert offer.product.owningOfferer == Offerer.query.get(offerer_id)

        @clean_database
        def when_creating_a_new_offer_from_an_existing_thing(self, app):
            # given
            user = create_user(email='user@test.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer)
            thing_product = create_product_with_Thing_type()
            PcObject.save(user_offerer, venue, thing_product)

            data = {
                'venueId': humanize(venue.id),
                'productId': humanize(thing_product.id)
            }
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')

            # when
            response = auth_request.post('/offers', json=data)

            # then
            assert response.status_code == 201

        @clean_database
        def when_creating_a_new_offer_from_an_existing_event(self, app):
            # given
            user = create_user(email='user@test.com')
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer)
            venue = create_venue(offerer)
            event_product = create_product_with_Event_type()
            PcObject.save(user_offerer, venue, event_product)

            data = {
                'venueId': humanize(venue.id),
                'productId': humanize(event_product.id)
            }
            auth_request = TestClient(app.test_client()).with_auth(email='user@test.com')

            # when
            response = auth_request.post('/offers', json=data)

            # then
            assert response.status_code == 201

        @clean_database
        def when_creating_a_new_activation_event_offer_as_a_global_admin(self, app):
            # Given
            user = create_user(email='test@email.com', can_book_free_offers=False, is_admin=True)
            offerer = create_offerer()
            venue = create_venue(offerer)
            PcObject.save(user, venue)

            json = {
                'name': "Offre d'activation",
                'durationMinutes': 60,
                'type': str(EventType.ACTIVATION),
                'venueId': humanize(venue.id),
            }

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 201

    class Returns403:
        @clean_database
        def when_creating_a_new_activation_event_offer_as_an_offerer_editor(self, app):
            # Given
            user = create_user(email='test@email.com', is_admin=False)
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer, is_admin=False)
            venue = create_venue(offerer)
            PcObject.save(user_offerer, venue)

            json = {
                'name': "Offre d'activation",
                'durationMinutes': 60,
                'type': str(EventType.ACTIVATION),
                'venueId': humanize(venue.id),
            }

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 403
            assert request.json['type'] == [
                "Seuls les administrateurs du pass Culture peuvent créer des offres d'activation"]

        @clean_database
        def when_creating_a_new_activation_event_offer_as_an_offerer_admin(self, app):
            # Given
            user = create_user(email='test@email.com', is_admin=False)
            offerer = create_offerer()
            user_offerer = create_user_offerer(user, offerer, is_admin=True)
            venue = create_venue(offerer)
            PcObject.save(user_offerer, venue)

            json = {
                'name': "Offre d'activation",
                'durationMinutes': 60,
                'type': str(EventType.ACTIVATION),
                'venueId': humanize(venue.id),
            }

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 403
            assert request.json['type'] == [
                "Seuls les administrateurs du pass Culture peuvent créer des offres d'activation"]

        @clean_database
        def when_user_is_not_attached_to_offerer(self, app):
            # Given
            user = create_user(email='test@email.com')
            offerer = create_offerer()
            venue = create_venue(offerer)
            PcObject.save(user, venue)

            json = {
                'name': 'La pièce de théâtre',
                'durationMinutes': 60,
                'type': str(EventType.SPECTACLE_VIVANT),
                'venueId': humanize(venue.id),
                'bookingEmail': 'offer@email.com'
            }

            # When
            request = TestClient(app.test_client()).with_auth(user.email).post(
                f'{API_URL}/offers',
                json=json)

            # Then
            assert request.status_code == 403
            assert request.json['global'] == ["Cette structure n'est pas enregistrée chez cet utilisateur."]
