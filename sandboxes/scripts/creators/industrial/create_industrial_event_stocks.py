from models.offer_type import EventType
from models.pc_object import PcObject
from utils.logger import logger
from utils.test_utils import create_stock_from_event_occurrence

EVENT_OCCURRENCE_STOCK_MODULO = 2

def create_industrial_event_stocks(event_occurrences_by_name):
    logger.info('create_industrial_event_stocks')

    event_stocks_by_name = {}

    event_occurrences = list(event_occurrences_by_name.items())
    event_occurrence_items_with_stocks = event_occurrences[::EVENT_OCCURRENCE_STOCK_MODULO]
    for event_occurrence_items_with_stocks in event_occurrence_items_with_stocks:
        (event_occurrence_with_stocks_name, event_occurrence_with_stocks) = event_occurrence_items_with_stocks
        available = 10

        if event_occurrence_with_stocks.offer.event.offerType['value'] == str(EventType.ACTIVATION):
            price = 0
        else:
            price = 10

        name = event_occurrence_with_stocks_name + " / " + str(available) + " / " + str(price)
        event_stocks_by_name[name] = create_stock_from_event_occurrence(
            event_occurrence_with_stocks,
            available=available,
            price=price
        )

    PcObject.check_and_save(*event_stocks_by_name.values())

    logger.info('created {} event_stocks'.format(len(event_stocks_by_name)))

    return event_stocks_by_name
