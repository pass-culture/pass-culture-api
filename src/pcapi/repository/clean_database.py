from pcapi import settings
from pcapi.core.bookings.models import Booking
from pcapi.core.offers.models import Mediation
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.core.users.models import User
from pcapi.local_providers.install import install_local_providers
from pcapi.models.activity import load_activity
from pcapi.models.allocine_pivot import AllocinePivot
from pcapi.models.allocine_venue_provider import AllocineVenueProvider
from pcapi.models.allocine_venue_provider_price_rule import AllocineVenueProviderPriceRule
from pcapi.models.api_key import ApiKey
from pcapi.models.bank_information import BankInformation
from pcapi.models.beneficiary_import import BeneficiaryImport
from pcapi.models.beneficiary_import_status import BeneficiaryImportStatus
from pcapi.models.criterion import Criterion
from pcapi.models.db import db
from pcapi.models.deposit import Deposit
from pcapi.models.email import Email
from pcapi.models.favorite_sql_entity import FavoriteSQLEntity
from pcapi.models.install import install_features
from pcapi.models.iris_france import IrisFrance
from pcapi.models.iris_venues import IrisVenues
from pcapi.models.local_provider_event import LocalProviderEvent
from pcapi.models.offer_criterion import OfferCriterion
from pcapi.models.offerer import Offerer
from pcapi.models.payment import Payment
from pcapi.models.payment_message import PaymentMessage
from pcapi.models.payment_status import PaymentStatus
from pcapi.models.product import Product
from pcapi.models.provider import Provider
from pcapi.models.user_offerer import UserOfferer
from pcapi.models.user_session import UserSession
from pcapi.models.venue_label_sql_entity import VenueLabelSQLEntity
from pcapi.models.venue_provider import VenueProvider
from pcapi.models.venue_sql_entity import VenueSQLEntity
from pcapi.models.venue_type import VenueType


def clean_all_database(*args, **kwargs):
    """ Order of deletions matters because of foreign key constraints """
    if settings.ENV not in ("development", "testing"):
        raise ValueError(f"You cannot do this on this environment: '{settings.ENV}'")
    Activity = load_activity()
    LocalProviderEvent.query.delete()
    AllocineVenueProviderPriceRule.query.delete()
    AllocineVenueProvider.query.delete()
    VenueProvider.query.delete()
    PaymentStatus.query.delete()
    Payment.query.delete()
    PaymentMessage.query.delete()
    Booking.query.delete()
    Stock.query.delete()
    FavoriteSQLEntity.query.delete()
    Mediation.query.delete()
    OfferCriterion.query.delete()
    Criterion.query.delete()
    Offer.query.delete()
    Product.query.delete()
    BankInformation.query.delete()
    IrisVenues.query.delete()
    IrisFrance.query.delete()
    VenueSQLEntity.query.delete()
    UserOfferer.query.delete()
    ApiKey.query.delete()
    Offerer.query.delete()
    Deposit.query.delete()
    BeneficiaryImportStatus.query.delete()
    BeneficiaryImport.query.delete()
    User.query.delete()
    Activity.query.delete()
    UserSession.query.delete()
    Email.query.delete()
    LocalProviderEvent.query.delete()
    Provider.query.delete()
    AllocinePivot.query.delete()
    VenueType.query.delete()
    VenueLabelSQLEntity.query.delete()
    db.session.commit()
    install_features()
    install_local_providers()
