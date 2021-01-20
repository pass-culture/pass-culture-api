from sqlalchemy import orm
from sqlalchemy.exc import ProgrammingError

from pcapi.models.db import db
from pcapi.models.db import versioning_manager
from pcapi.models.feature import FEATURES_DISABLED_BY_DEFAULT
from pcapi.models.feature import Feature
from pcapi.models.feature import FeatureToggle
from pcapi.repository import repository


def install_models() -> None:
    """Make SQLAlchemy aware of our models."""
    # pylint: disable=unused-import
    from pcapi.core.bookings.models import Booking
    from pcapi.core.offers.models import Mediation
    from pcapi.core.offers.models import Offer
    from pcapi.core.offers.models import Stock
    from pcapi.core.users.models import Token
    from pcapi.core.users.models import User
    from pcapi.models.allocine_pivot import AllocinePivot
    from pcapi.models.allocine_venue_provider import AllocineVenueProvider
    from pcapi.models.allocine_venue_provider_price_rule import AllocineVenueProviderPriceRule
    from pcapi.models.api_errors import ApiErrors
    from pcapi.models.api_key import ApiKey
    from pcapi.models.bank_information import BankInformation
    from pcapi.models.beneficiary_import import BeneficiaryImport
    from pcapi.models.beneficiary_import import BeneficiaryImportSources
    from pcapi.models.beneficiary_import_status import BeneficiaryImportStatus
    from pcapi.models.beneficiary_import_status import ImportStatus
    from pcapi.models.criterion import Criterion
    from pcapi.models.db import db
    from pcapi.models.deactivable_mixin import DeactivableMixin
    from pcapi.models.deposit import Deposit
    from pcapi.models.email import Email
    from pcapi.models.extra_data_mixin import ExtraDataMixin
    from pcapi.models.favorite_sql_entity import FavoriteSQLEntity
    from pcapi.models.feature import Feature
    from pcapi.models.has_address_mixin import HasAddressMixin
    from pcapi.models.has_thumb_mixin import HasThumbMixin
    from pcapi.models.iris_france import IrisFrance
    from pcapi.models.iris_venues import IrisVenues
    from pcapi.models.local_provider_event import LocalProviderEvent
    from pcapi.models.needs_validation_mixin import NeedsValidationMixin
    from pcapi.models.offer_criterion import OfferCriterion
    from pcapi.models.offer_type import EventType
    from pcapi.models.offer_type import ThingType
    from pcapi.models.offerer import Offerer
    from pcapi.models.payment import Payment
    from pcapi.models.payment_message import PaymentMessage
    from pcapi.models.payment_status import PaymentStatus
    from pcapi.models.pc_object import PcObject
    from pcapi.models.product import BookFormat
    from pcapi.models.product import Product
    from pcapi.models.providable_mixin import ProvidableMixin
    from pcapi.models.provider import Provider
    from pcapi.models.user_offerer import RightsType
    from pcapi.models.user_offerer import UserOfferer
    from pcapi.models.user_session import UserSession
    from pcapi.models.venue_label_sql_entity import VenueLabelSQLEntity
    from pcapi.models.venue_provider import VenueProvider
    from pcapi.models.venue_sql_entity import VenueSQLEntity
    from pcapi.models.venue_type import VenueType
    from pcapi.models.versioned_mixin import VersionedMixin


def install_activity() -> None:
    orm.configure_mappers()

    create_versionning_tables()

    db.session.commit()


def install_features() -> None:
    Feature.query.delete()
    features = []
    for toggle in FeatureToggle:
        isActive = toggle not in FEATURES_DISABLED_BY_DEFAULT
        feature = Feature(name=toggle.name, description=toggle.value, isActive=isActive)
        features.append(feature)
    repository.save(*features)


def create_versionning_tables() -> None:
    # FIXME: This is seriously ugly... (based on https://github.com/kvesteri/postgresql-audit/issues/21)
    try:
        versioning_manager.transaction_cls.__table__.create(db.session.get_bind())
    except ProgrammingError:
        pass
    try:
        versioning_manager.activity_cls.__table__.create(db.session.get_bind())
    except ProgrammingError:
        pass
