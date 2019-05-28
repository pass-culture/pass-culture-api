from models.offer_type import EventType
from models.pc_object import PcObject
from sandboxes.scripts.utils.select import remove_every
from utils.logger import logger
from tests.test_utils import create_stock_from_event_occurrence, get_price_by_short_name, get_occurrence_short_name

EVENT_OCCURRENCES_WITH_STOCKS_REMOVE_MODULO = 4

def create_industrial_event_stocks(event_occurrences_by_name):
    logger.info('create_industrial_event_stocks')

    event_stocks_by_name = {}
    short_names_to_increase_price = []

    event_occurrence_items = list(event_occurrences_by_name.items())

    event_occurrence_items_with_stocks = remove_every(
        event_occurrence_items,
        EVENT_OCCURRENCES_WITH_STOCKS_REMOVE_MODULO
    )

    for event_occurrence_item_with_stocks in event_occurrence_items_with_stocks:
        (
            event_occurrence_with_stocks_name,
            event_occurrence_with_stocks
        ) = event_occurrence_item_with_stocks
        available = 10

        short_name = get_occurrence_short_name(
          event_occurrence_with_stocks_name
        )
        price = get_price_by_short_name(short_name)
        fcount = short_names_to_increase_price.count(short_name)
        if (fcount > 2):
          price = price + fcount
        short_names_to_increase_price.append(short_name)

        if event_occurrence_with_stocks['offer'].product.offerType['value'] == str(EventType.ACTIVATION):
            price = 0

        name = event_occurrence_with_stocks_name + " / " + str(available) + " / " + str(price)

        event_stocks_by_name[name] = create_stock_from_event_occurrence(
            event_occurrence_with_stocks,
            available=available,
            price=price
        )

    PcObject.save(*event_stocks_by_name.values())

    logger.info('created {} event_stocks'.format(len(event_stocks_by_name)))

    return event_stocks_by_name
