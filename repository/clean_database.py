from local_providers.install import install_local_providers
from models.activity import load_activity
from models.beneficiary_import import BeneficiaryImport
from models.db import db
from models import Booking, \
    Deposit, \
    Mediation, \
    Payment, \
    PaymentStatus, \
    Product, \
    Offer, \
    Offerer, \
    Recommendation, \
    Stock, \
    User, \
    UserOfferer, \
    UserSession, \
    Venue, \
    Provider, \
    VenueProvider, PaymentMessage, BankInformation, LocalProviderEvent, Feature, Favorite
from models.email import Email
from models.install import install_features


def clean_all_database(*args, **kwargs):
    """ Order of deletions matters because of foreign key constraints """
    Activity = load_activity()
    LocalProviderEvent.query.delete()
    VenueProvider.query.delete()
    PaymentStatus.query.delete()
    Payment.query.delete()
    PaymentMessage.query.delete()
    Booking.query.delete()
    Stock.query.delete()
    Favorite.query.delete()
    Recommendation.query.delete()
    Mediation.query.delete()
    Offer.query.delete()
    Product.query.delete()
    BankInformation.query.delete()
    Venue.query.delete()
    UserOfferer.query.delete()
    Offerer.query.delete()
    Deposit.query.delete()
    BeneficiaryImport.query.delete()
    User.query.delete()
    Activity.query.delete()
    UserSession.query.delete()
    Email.query.delete()
    LocalProviderEvent.query.delete()
    Feature.query.delete()
    Provider.query.delete()
    db.session.commit()

    install_features()
    install_local_providers()

