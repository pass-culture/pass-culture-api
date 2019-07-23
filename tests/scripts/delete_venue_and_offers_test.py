import pytest

from models import PcObject, Venue, Offer
from scripts.delete_venue_and_offers_for_venue_id import delete_venue_and_offers_for_venue_id
from tests.conftest import clean_database
from tests.test_utils import create_venue, create_offerer, create_offer_with_event_product, create_stock
from utils.human_ids import humanize


class DeleteVenueAndOffersForVenueIdTest:
    @clean_database
    def test_delete_venue_and_offers_should_delete_venue_and_offers_with_venue_id(self, app):
        # Given
        offerer1 = create_offerer("123456789")
        offerer2 = create_offerer("111111111")
        venue1 = create_venue(
            offerer1,
            idx=1,
            siret='12345678900002',
            address='1 rue Vieille Adresse',
            name='Vieux nom',
            city='Vieilleville',
            latitude='48.863',
            longitude='2.36',
            postal_code='75001')
        venue2 = create_venue(
            offerer2,
            idx=2,
            siret='12345678900003',
            address='1 rue de valois',
            name='super nom',
            city='Paris',
            latitude='48.890',
            longitude='2.40',
            postal_code='92000')
        offer1 = create_offer_with_event_product(venue1)
        offer2 = create_offer_with_event_product(venue2)
        offer3 = create_offer_with_event_product(venue1)
        PcObject.save(offer1, offer2, offer3, venue1, venue2)

        # When
        delete_venue_and_offers_for_venue_id(humanize(venue1.id))

        # Then
        venue1 = Venue.query.filter_by(id=venue1.id).first()
        venue2 = Venue.query.filter_by(id=venue2.id).first()
        offer1 = Offer.query.filter_by(id=offer1.id).first()
        offer2 = Offer.query.filter_by(id=offer2.id).first()
        offer3 = Offer.query.filter_by(id=offer3.id).first()
        assert offer1 is None
        assert offer3 is None
        assert venue1 is None
        assert offer2 is not None
        assert venue2 is not None

    @clean_database
    def test_delete_venue_and_offers_should_raise_an_attribute_error_when_at_least_one_offer_has_stocks(self, app):
        # Given
        offerer = create_offerer("123456789")
        venue = create_venue(
            offerer,
            idx=1,
            siret='12345678900002',
            address='1 rue Vieille Adresse',
            name='Vieux nom',
            city='Vieilleville',
            latitude='48.863',
            longitude='2.36',
            postal_code='75001')
        offer1 = create_offer_with_event_product(venue)
        offer2 = create_offer_with_event_product(venue)
        stock = create_stock(offer=offer1)

        PcObject.save(offer1, offer2, stock, venue)

        # When
        with pytest.raises(AttributeError) as e:
            delete_venue_and_offers_for_venue_id(humanize(venue.id))

        # Then
        assert str(e.value) == 'Offres non supprimables car au moins une contient des stocks'
