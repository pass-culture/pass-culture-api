from datetime import datetime, timedelta
from decimal import Decimal

from freezegun import freeze_time

from algolia.infrastructure.builder import build_object
from models import EventType
from repository import repository
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_offerer, create_stock, create_venue
from tests.model_creators.specific_creators import create_offer_with_event_product, create_offer_with_thing_product
from utils.human_ids import humanize


class BuildObjectTest:
    @clean_database
    @freeze_time('2020-10-15 09:00:00')
    def test_should_return_algolia_object_with_required_information(self, app):
        # Given
        in_four_days = datetime.utcnow() + timedelta(days=4)
        three_days_ago = datetime.utcnow() + timedelta(days=-3)
        offerer = create_offerer(name='Offerer name', idx=1)
        venue = create_venue(offerer=offerer,
                             city='Paris',
                             idx=2,
                             latitude=48.8638689,
                             longitude=2.3380198,
                             name='Venue name',
                             public_name='Venue public name')
        offer = create_offer_with_event_product(venue=venue,
                                                description='Un lit sous une rivière',
                                                idx=3,
                                                is_active=True,
                                                event_name='Event name',
                                                event_type=EventType.MUSIQUE,
                                                thumb_count=1,
                                                date_created=datetime(2020, 1, 1, 10, 0, 0))
        stock1 = create_stock(quantity=10,
                              beginning_datetime=in_four_days,
                              offer=offer,
                              price=10)
        stock2 = create_stock(quantity=10,
                              beginning_datetime=in_four_days,
                              offer=offer,
                              price=20)
        stock3 = create_stock(quantity=10,
                              beginning_datetime=in_four_days,
                              offer=offer,
                              price=0)
        stock4 = create_stock(quantity=10,
                              beginning_datetime=in_four_days,
                              is_soft_deleted=True,
                              offer=offer,
                              price=0)
        stock5 = create_stock(quantity=10,
                              beginning_datetime=three_days_ago,
                              offer=offer,
                              price=0)
        repository.save(stock1, stock2, stock3, stock4, stock5)
        humanized_product_id = humanize(offer.product.id)

        # When
        result = build_object(offer)

        # Then
        assert result == {
            'objectID': 'AM',
            'offer': {
                'author': None,
                'category': 'MUSIQUE',
                'dateCreated': 1577872800.0,
                'dates': [1603098000.0, 1603098000.0, 1603098000.0],
                'description': 'Un lit sous une rivière',
                'id': 'AM',
                'isbn': None,
                'isDuo': False,
                'isDigital': False,
                'isEvent': True,
                'isThing': False,
                'label': 'Concert ou festival',
                'name': 'Event name',
                'musicSubType': None,
                'musicType': None,
                'performer': None,
                'prices': [Decimal('0.00'), Decimal('10.00'), Decimal('20.00')],
                'priceMin': Decimal('0.00'),
                'priceMax': Decimal('20.00'),
                'showSubType': None,
                'showType': None,
                'speaker': None,
                'stageDirector': None,
                'thumbUrl': f'http://localhost/storage/thumbs/products/{humanized_product_id}',
                'type': 'Écouter',
                'visa': None,
            },
            'offerer': {
                'name': 'Offerer name',
            },
            'venue': {
                'city': 'Paris',
                'departementCode': '93',
                'name': 'Venue name',
                'publicName': 'Venue public name'
            },
            '_geoloc': {
                'lat': 48.86387,
                'lng': 2.33802
            }
        }

    @clean_database
    def test_should_return_an_author_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'author': 'MEFA'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['author'] == 'MEFA'

    @clean_database
    def test_should_return_a_stage_director_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'stageDirector': 'MEFA'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['stageDirector'] == 'MEFA'

    @clean_database
    def test_should_return_a_visa_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'visa': '123456789'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['visa'] == '123456789'

    @clean_database
    def test_should_return_an_isbn_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'isbn': '123456789'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['isbn'] == '123456789'

    @clean_database
    def test_should_return_a_speaker_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'speaker': 'MEFA'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['speaker'] == 'MEFA'

    @clean_database
    def test_should_return_a_performer_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'performer': 'MEFA'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['performer'] == 'MEFA'

    @clean_database
    def test_should_return_a_show_type_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'showType': 'dance'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['showType'] == 'dance'

    @clean_database
    def test_should_return_a_show_sub_type_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'showSubType': 'urbaine'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['showSubType'] == 'urbaine'

    @clean_database
    def test_should_return_a_music_type_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'musicType': 'jazz'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['musicType'] == 'jazz'

    @clean_database
    def test_should_return_a_music_sub_type_when_exists(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        offer.extraData = {'musicSubType': 'fusion'}
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['musicSubType'] == 'fusion'

    @clean_database
    def test_should_return_the_first_stock_price(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        stock1 = create_stock(offer=offer, price=7)
        stock2 = create_stock(offer=offer, price=5)
        stock3 = create_stock(offer=offer, price=10.3)
        repository.save(stock1, stock2, stock3)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['prices'] == [Decimal('5.00'), Decimal('7.00'), Decimal('10.30')]

    @clean_database
    def test_should_not_return_coordinates_when_one_coordinate_is_missing(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer, latitude=None, longitude=12.13)
        offer = create_offer_with_thing_product(venue=venue)
        stock = create_stock(offer=offer)
        repository.save(stock)

        # When
        result = build_object(offer)

        # Then
        assert '_geoloc' not in result

    @freeze_time('2020-10-15 09:00:00')
    @clean_database
    def test_should_return_event_beginning_datetimes_as_timestamp_sorted_from_oldest_to_newest_when_event(self, app):
        # Given
        in_three_days = datetime.utcnow() + timedelta(days=3)
        in_four_days = datetime.utcnow() + timedelta(days=4)
        in_five_days = datetime.utcnow() + timedelta(days=5)
        in_ten_days = datetime.utcnow() + timedelta(days=10)
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_event_product(venue=venue)
        stock1 = create_stock(beginning_datetime=in_four_days, offer=offer)
        stock2 = create_stock(beginning_datetime=in_three_days, offer=offer)
        stock3 = create_stock(beginning_datetime=in_ten_days, offer=offer)
        stock4 = create_stock(beginning_datetime=in_five_days, offer=offer)
        repository.save(stock1, stock2, stock3, stock4)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['dates'] == [1603011600.0, 1603098000.0, 1603184400.0, 1603616400.0]

    @clean_database
    def test_should_not_return_event_beginning_datetimes_as_timestamp_when_thing(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer=offerer)
        offer = create_offer_with_thing_product(venue=venue)
        stock1 = create_stock(offer=offer)
        stock2 = create_stock(offer=offer)
        repository.save(stock1, stock2)

        # When
        result = build_object(offer)

        # Then
        assert result['offer']['dates'] == []
