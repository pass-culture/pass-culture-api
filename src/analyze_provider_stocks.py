from pcapi.core.offerers.models import Venue
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.local_providers.provider_api import synchronize_provider_api
from pcapi.models.offer_type import ThingType
from pcapi.models.product import Product
from pcapi.utils.human_ids import dehumanize
from pcapi.utils.human_ids import humanize


VENUE_ID = dehumanize("L92A")
# ISBN = "9782820338013"


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]


class AnalyzeStocks:
    def __init__(self, venue_id):
        self.provider_stocks = set()
        self.available_stocks = set()
        self.existing_products = set()
        self.gcu_compatible_products = set()
        self.existing_offers = set()
        self.existing_stocks = set()
        self.unbooked_offers = set()
        self.active_offers = set()
        venue = Venue.query.get(VENUE_ID)
        self.venue_provider = venue.venueProviders[0]
        provider = self.venue_provider.provider
        provider_api = provider.getProviderAPI()
        for raw_stocks in synchronize_provider_api._get_stocks_by_batch(venue.siret, provider_api, None):
            for stock in raw_stocks:
                self.provider_stocks.add(stock["ref"])
                if stock["available"] > 0:
                    self.available_stocks.add(stock["ref"])
        for isbns in batch(list(self.available_stocks), 1000):
            products = (
                Product.query.filter(Product.type == str(ThingType.LIVRE_EDITION))
                .filter(Product.idAtProviders.in_(isbns))
                .with_entities(Product.id, Product.isGcuCompatible)
                .all()
            )
            for (idx, gcu_compatible) in products:
                self.existing_products.add(idx)
                if gcu_compatible:
                    self.gcu_compatible_products.add(idx)
        for product_ids in batch(list(self.gcu_compatible_products), 1000):
            offers = (
                Offer.query.filter(Offer.productId.in_(product_ids))
                .filter(Offer.venueId == VENUE_ID)
                .with_entities(Offer.id)
                .all()
            )
            for (idx,) in offers:
                self.existing_offers.add(idx)
        for offer_ids in batch(list(self.existing_offers), 1000):
            stocks = (
                Stock.query.filter(Stock.offerId.in_(offer_ids))
                .with_entities(Stock.id, Stock.quantity, Stock.dnBookedQuantity, Stock.offerId)
                .all()
            )
            for (idx, quantity, booked_quantity, offer_id) in stocks:
                self.existing_stocks.add(idx)
                if quantity > booked_quantity:
                    self.unbooked_offers.add(offer_id)
        for offer_ids in batch(list(self.unbooked_offers), 1000):
            offers = Offer.query.filter(Offer.id.in_(offer_ids)).with_entities(Offer.id, Offer.isActive).all()
            for (idx, is_active) in offers:
                if is_active:
                    self.active_offers.add(idx)
        print(self.results())
    def results(self):
        return f"""
-- Analyse terminée --

Pour la librairie {self.venue_provider.venue.publicName or self.venue_provider.venue.name} on a :

{len(self.provider_stocks)} EAN ont été reçus de l'api fournisseur {self.venue_provider.provider.name}.
{len(self.available_stocks)} EAN ont une quantité supérieure à 0.
{len(self.existing_products)} sont dans notre base produit.
{len(self.gcu_compatible_products)} correspondent à des produits compatibles avec nos GCU.
{len(self.existing_offers)} sont dans les offres de la librairie.
{len(self.existing_stocks)} sont dans les stocks de la librairie.
{len(self.unbooked_offers)} ont une quantité de stock disponible supérieure au nombre de réservations en attente sur le pass.
{len(self.active_offers)} sont actives.

C'est ce qu'on observe sur le compte de la structure ? https://pro.passculture.beta.gouv.fr/accueil?structure={humanize(self.venue_provider.venue.managingOffererId)}
"""


AnalyzeStocks(VENUE_ID)
