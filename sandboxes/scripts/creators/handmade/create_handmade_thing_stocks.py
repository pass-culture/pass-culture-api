from models.pc_object import PcObject
from utils.logger import logger
from tests.test_utils import create_stock_from_offer

def create_handmade_thing_stocks(offers_by_name):
    logger.info("create_handmade_thing_stocks")

    thing_stocks_by_name = {}

    thing_stocks_by_name['Ravage / THEATRE DE L ODEON / 50 / 50'] = create_stock_from_offer(
        offers_by_name['Ravage / THEATRE DE L ODEON'],
        available=50,
        price=50
    )

    thing_stocks_by_name['pass Culture Activation / ACTIVATION (Offre en ligne) / 15000 / 0'] = create_stock_from_offer(
        offers_by_name['pass Culture Activation / Activation (Offre en ligne)'],
        available=15000,
        price=0
    )

    PcObject.check_and_save(*offers_by_name.values())

    logger.info('created {} hing_stocks'.format(len(thing_stocks_by_name)))

    return thing_stocks_by_name
