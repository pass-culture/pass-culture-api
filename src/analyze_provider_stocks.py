from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.utils.human_ids import dehumanize
from pcapi.utils.human_ids import humanize


VENUE_ID = dehumanize("GBBQ")

from pcapi.core.offerers.models import Venue
from pcapi.local_providers.provider_api import synchronize_provider_api
from pcapi.models.offer_type import ThingType
from pcapi.models.product import Product


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]


venue = Venue.query.get(VENUE_ID)

venue_provider = venue.venueProviders[0]
provider = venue_provider.provider
provider_api = provider.getProviderAPI()

provider_stocks = set()
available_stocks = set()
for raw_stocks in synchronize_provider_api._get_stocks_by_batch(venue.siret, provider_api, None):
    for stock in raw_stocks:
        provider_stocks.add(stock["ref"])
        if stock["available"] > 0:
            available_stocks.add(stock["ref"])


existing_products = set()
gcu_compatible_products = set()
for isbns in batch(list(available_stocks), 1000):
    products = (
        Product.query.filter(Product.type == str(ThingType.LIVRE_EDITION))
        .filter(Product.idAtProviders.in_(isbns))
        .with_entities(Product.id, Product.isGcuCompatible)
        .all()
    )
    for (idx, gcu_compatible) in products:
        existing_products.add(idx)
        if gcu_compatible:
            gcu_compatible_products.add(idx)

existing_offers = set()
for product_ids in batch(list(gcu_compatible_products), 1000):
    offers = (
        Offer.query.filter(Offer.productId.in_(product_ids))
        .filter(Offer.venueId == VENUE_ID)
        .with_entities(Offer.id)
        .all()
    )
    for (idx,) in offers:
        existing_offers.add(idx)

existing_stocks = set()
unbooked_offers = set()
for offer_ids in batch(list(existing_offers), 1000):
    stocks = (
        Stock.query.filter(Stock.offerId.in_(offer_ids))
        .with_entities(Stock.id, Stock.quantity, Stock.dnBookedQuantity, Stock.offerId)
        .all()
    )
    for (idx, quantity, booked_quantity, offer_id) in stocks:
        existing_stocks.add(idx)
        if quantity > booked_quantity:
            unbooked_offers.add(offer_id)

active_offers = set()
for offer_ids in batch(list(unbooked_offers), 1000):
    offers = Offer.query.filter(Offer.id.in_(offer_ids)).with_entities(Offer.id, Offer.isActive).all()
    for (idx, is_active) in offers:
        if is_active:
            active_offers.add(idx)


print(
    f"""
Analyse terminée :

{len(provider_stocks)} EAN ont été reçus de l'api fournisseur {provider.name}.
{len(available_stocks)} EAN ont une quantité supérieure à 0.
{len(existing_products)} sont dans notre base produit.
{len(gcu_compatible_products)} correspondent à des produits compatibles avec nos GCU.
{len(existing_offers)} sont dans les offres de la librairie.
{len(existing_stocks)} sont dans les stocks de la librairie.
{len(unbooked_offers)} ont une quantité de stock disponible supérieure au nombre de réservations en attente sur le pass.
{len(active_offers)} sont actives.

C'est ce qu'on observe sur le compte de la structure ? https://pro.passculture.beta.gouv.fr/accueil?structure={humanize(venue.managingOffererId)}
"""
)
