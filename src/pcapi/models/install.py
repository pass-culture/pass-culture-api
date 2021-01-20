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
    import pcapi.core.bookings.models
    import pcapi.core.offers.models
    import pcapi.core.users.models
    import pcapi.models.allocine_pivot
    import pcapi.models.allocine_venue_provider
    import pcapi.models.allocine_venue_provider_price_rule
    import pcapi.models.api_key
    import pcapi.models.bank_information
    import pcapi.models.beneficiary_import
    import pcapi.models.beneficiary_import_status
    import pcapi.models.criterion
    import pcapi.models.deposit
    import pcapi.models.email
    import pcapi.models.extra_data_mixin
    import pcapi.models.favorite_sql_entity
    import pcapi.models.feature
    import pcapi.models.iris_france
    import pcapi.models.iris_venues
    import pcapi.models.local_provider_event
    import pcapi.models.offer_criterion
    import pcapi.models.offerer
    import pcapi.models.payment
    import pcapi.models.payment_message
    import pcapi.models.payment_status
    import pcapi.models.product
    import pcapi.models.providable_mixin
    import pcapi.models.provider
    import pcapi.models.user_offerer
    import pcapi.models.user_session
    import pcapi.models.venue_label_sql_entity
    import pcapi.models.venue_provider
    import pcapi.models.venue_sql_entity
    import pcapi.models.venue_type
    import pcapi.models.versioned_mixin


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
