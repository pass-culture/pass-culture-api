from sqlalchemy import func

from models import PcObject, ApiErrors
from models import Venue
from models.db import db
from models.venue import TooManyVirtualVenuesException
from utils.file import read_file
from utils.logger import logger


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
        api_errors = ApiErrors()
        api_errors.addError('isVirtual', 'Un lieu pour les offres numériques existe déjà pour cette structure')
        raise api_errors

def save_venue_rib(venue):
    api_errors = ApiErrors()
    try:
        rib_file = read_file('rib')
        venue.save_thumb(rib_file, 0)
    except ValueError as e:
        logger.error(e)
        api_errors.addError('rib', "Le rib n'a pas un bon format")
        raise api_errors

def find_by_id(venue_id):
    return Venue.query.filter_by(id=venue_id).first()
