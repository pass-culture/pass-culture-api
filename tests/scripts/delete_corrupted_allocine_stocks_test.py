from models import PcObject, Stock
from repository.provider_queries import get_provider_by_local_class
from scripts.delete_corrupted_allocine_stocks import delete_corrupted_allocine_stocks
from tests.conftest import clean_database
from tests.model_creators.generic_creators import create_stock, create_offerer, create_venue
from tests.model_creators.specific_creators import create_offer_with_thing_product


class DeleteCorruptedAllocineStocksTest:
    @clean_database
    def test_should_delete_stock_from_allocine_provider_with_specific_id_at_provider_format(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        allocine_provider = get_provider_by_local_class('AllocineStocks')
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer,
                             last_provider_id=allocine_provider.id,
                             id_at_providers='TW92aWU6MjczNjU5%38986972800011-1',
                             is_soft_deleted=True)
        PcObject.save(stock)

        # When
        delete_corrupted_allocine_stocks()

        # Then
        assert Stock.query.count() == 0

    @clean_database
    def test_should_not_delete_stock_from_allocine_with_new_id_format(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        allocine_provider = get_provider_by_local_class('AllocineStocks')
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer,
                             last_provider_id=allocine_provider.id,
                             id_at_providers='TW92aWU6MjczNTc5%31940406700021#LOCAL/2020-01-18T14:00:00',
                             is_soft_deleted=True)
        PcObject.save(stock)

        # When
        delete_corrupted_allocine_stocks()

        # Then
        assert Stock.query.count() == 1

    @clean_database
    def test_should_not_delete_stock_from_other_provider_than_allocine(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        titelive_provider = get_provider_by_local_class('TiteLiveStocks')
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer,
                             last_provider_id=titelive_provider.id,
                             id_at_providers='TW92aWU6MjczNjU5%38986972800011-1',
                             is_soft_deleted=True)
        PcObject.save(stock)

        # When
        delete_corrupted_allocine_stocks()

        # Then
        assert Stock.query.count() == 1

    @clean_database
    def test_should_not_delete_stock_from_allocine_when_not_sof_deleted(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        allocine_provider = get_provider_by_local_class('AllocineStocks')
        offer = create_offer_with_thing_product(venue)
        stock = create_stock(offer=offer,
                             last_provider_id=allocine_provider.id,
                             id_at_providers='TW92aWU6MjczNjU5%38986972800011-1',
                             is_soft_deleted=False)
        PcObject.save(stock)

        # When
        delete_corrupted_allocine_stocks()

        # Then
        assert Stock.query.count() == 1
