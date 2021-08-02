import logging

from pcapi.core.offerers import models as offerers_models
from pcapi.core.offerers.factories import VenueTypeFactory
from pcapi.models import db


logger = logging.getLogger(__name__)


def create_industrial_venue_types() -> list[offerers_models.VenueType]:
    logger.info("create_industrial_venue_types")

    venue_types_data = get_venue_types_data()
    venue_types = [VenueTypeFactory(code=code, label=label) for code, label in venue_types_data]

    logger.info("created %i venue types", len(venue_types))

    return venue_types


def update_industrial_venue_types(commit: bool = True) -> None:
    """
    Helper function that runs a data migration for an existing environment that
    ran the previous version of create_industrial_venue_types which was written
    before venue_type has a code column.

    Note: the function uses db.session which could handle other pending
    objects. Pass commit=False if you don't want to run a commit at the end of
    this function.
    """
    logger.info("update_industrial_venue_types")

    venue_types_data = get_venue_types_data()
    for code, label in venue_types_data:
        venue_type = offerers_models.VenueType.query.filter_by(label=label).one()
        venue_type.code = code
        db.session.add(venue_type)

    if commit:
        db.session.commit()

    logger.info("updated %i venue types", len(venue_types_data))


def get_venue_types_data() -> list[tuple[str, str]]:
    return [(e.name, e.value) for e in offerers_models.VenueTypeEnum]
