from datetime import timedelta

from models.offer_type import EventType
from models.pc_object import PcObject
from sandboxes.scripts.utils.select import remove_every
from utils.date import strftime, today
from utils.logger import logger
from tests.test_utils import create_stock_from_offer, \
                             get_price_by_short_name, \
                             get_occurrence_short_name

EVENT_OCCURRENCE_BEGINNING_DATETIMES = [
    today,
    today + timedelta(days=2),
    today + timedelta(days=2, hours=2),
    today + timedelta(days=15)
]

EVENT_OFFERS_WITH_STOCKS_REMOVE_MODULO = 3

def create_industrial_event_stocks(event_offers_by_name):
    logger.info('create_industrial_event_stocks')

    event_stocks_by_name = {}
    short_names_to_increase_price = []

    event_offer_items = list(event_offers_by_name.items())

    event_offer_items_with_stocks = remove_every(
        event_offer_items,
        EVENT_OFFERS_WITH_STOCKS_REMOVE_MODULO
    )

    for (index, event_offer_item_with_stocks) in enumerate(event_offer_items_with_stocks):

        event_offer_with_stocks_name = event_offer_item_with_stocks[0]
        event_offer_with_stocks = event_offer_item_with_stocks[1]
        product = event_offer_with_stocks.product

        available = 10

        short_name = get_occurrence_short_name(event_offer_with_stocks_name)
        price = get_price_by_short_name(short_name)
        fcount = short_names_to_increase_price.count(short_name)
        if (fcount > 2):
          price = price + fcount
        short_names_to_increase_price.append(short_name)
        if product.offerType['value'] == str(EventType.ACTIVATION):
            price = 0

        for beginning_datetime in beginning_datetimes:
            name = "{} / {} / {} / {}".format(
                event_offer_with_stocks_name,
                strftime(beginning_datetime),
                available,
                price
            )
            event_stocks_by_name[name] = create_stock_from_offer(
                event_offer_with_stocks,
                available=available,
                beginning_datetime=strftime(beginning_datetime),
                end_datetime=strftime(beginning_datetime + timedelta(hours=1)),
                price=price
            )

    PcObject.save(*event_stocks_by_name.values())

    logger.info('created {} event_stocks'.format(len(event_stocks_by_name)))

    return event_stocks_by_name
