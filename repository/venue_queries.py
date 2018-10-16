from sqlalchemy import func

from models import PcObject, ApiErrors
from models import Venue
from models.db import db
from models.venue import TooManyVirtualVenuesException


def count_venues_by_departement():
    result = db.session.query(Venue.departementCode, func.count(Venue.id)) \
        .group_by(Venue.departementCode) \
        .order_by(Venue.departementCode) \
        .all()
    return result


def save_venue(venue):
    try:
        PcObject.check_and_save(venue)
    except TooManyVirtualVenuesException:
        errors = ApiErrors()
        errors.addError('isVirtual', 'Un lieu pour les offres numériques existe déjà pour cette structure')
        raise errors

def save_venue_rib(venue):
    try:
        venue.save_thumb(read_file('rib'), 0)
    except ValueError as e:
        logger.error(e)
        api_errors.addError('rib', "Le rib n'a pas un bon format")
        raise api_errors

def find_by_id(venue_id):
    return Venue.query.filter_by(id=venue_id).first()
