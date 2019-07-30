from models import PcObject, Provider, ThingType
from sandboxes.ScenarioBuilder import ScenarioBuilder
from utils.logger import logger


def create_pro_account_with_products_from_tite_live():
    logger.info('[START] Create a pro account with offers that comes from TiteLive')

    tite_live_provider = Provider \
        .query \
        .filter(Provider.localClass == 'TiteLiveThings') \
        .first()

    pro_email = "pctest.pro{}.titelive@btmx.fr".format(78)

    scenario = ScenarioBuilder() \
        .with_user_pro('Jean', 'Dupont') \
        .detail('email', pro_email) \
        .with_offerer('chapitre', siren='912365488') \
        .with_venue('chez Zola') \
        .detail('departementCode', 78) \
        .with_offer() \
        .detail('type', str(ThingType.LIVRE_EDITION)) \
        .detail('lastProviderId', tite_live_provider.id) \
        .build()

    PcObject.save(scenario)

    logger.info('[END] Create a pro account with offers that comes from TiteLive')
