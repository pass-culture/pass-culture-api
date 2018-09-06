""" venue """
from sqlalchemy.event import listens_for
from sqlalchemy import BigInteger, \
    Column, \
    ForeignKey, \
    Index, \
    Numeric, \
    String, \
    TEXT, Boolean, CheckConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.functions import coalesce

from models.db import Model
from models.has_address_mixin import HasAddressMixin
from models.has_thumb_mixin import HasThumbMixin
from models.offer import Offer
from models.offerer import Offerer
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin
from utils.search import create_tsvector

CONSTRAINT_CHECK_IS_VIRTUAL_XOR_HAS_ADDRESS = """
(
    "isVirtual" IS TRUE
    AND (address IS NULL AND "postalCode" IS NULL AND city IS NULL AND "departementCode" IS NULL)
)
OR
(
    "isVirtual" IS FALSE
    AND (address IS NOT NULL AND "postalCode" IS NOT NULL AND city IS NOT NULL AND "departementCode" IS NOT NULL)
)
"""


class Venue(PcObject,
            HasThumbMixin,
            HasAddressMixin,
            ProvidableMixin,
            Model):
    id = Column(BigInteger, primary_key=True)

    name = Column(String(140), nullable=False)

    siret = Column(String(14), nullable=True, unique=True)

    departementCode = Column(String(3), nullable=True, index=True)

    latitude = Column(Numeric(8, 5), nullable=True)

    longitude = Column(Numeric(8, 5), nullable=True)

    venueProviders = relationship('VenueProvider',
                                  back_populates="venue")

    managingOffererId = Column(BigInteger,
                               ForeignKey("offerer.id"),
                               nullable=False,
                               index=True)

    managingOfferer = relationship('Offerer',
                                   foreign_keys=[managingOffererId],
                                   backref='managedVenues')

    bookingEmail = Column(String(120), nullable=True)

    address = Column(String(200), nullable=True)

    postalCode = Column(String(6), nullable=True)

    city = Column(String(50), nullable=True)

    isVirtual = Column(
        Boolean,
        CheckConstraint(CONSTRAINT_CHECK_IS_VIRTUAL_XOR_HAS_ADDRESS, name='check_is_virtual_xor_has_address'),
        nullable=False,
        default=False
    )

    # openingHours = Column(ARRAY(TIME))
    # Ex: [['09:00', '18:00'], ['09:00', '19:00'], null,  ['09:00', '18:00']]
    # means open monday 9 to 18 and tuesday 9 to 19, closed wednesday,
    # open thursday 9 to 18, closed the rest of the week

    def store_department_code(self):
        self.departementCode = self.postalCode[:-3]

    def errors(self):
        api_errors = super(Venue, self).errors()

        if self.siret is not None \
                and not len(self.siret) == 14:
            api_errors.addError('siret', 'Ce code SIRET est invalide : ' + self.siret)
        if self.managingOffererId is not None:
            if self.managingOfferer is None:
                managingOfferer = Offerer.query \
                    .filter_by(id=self.managingOffererId).first()
            else:
                managingOfferer = self.managingOfferer
            if managingOfferer.siren is None:
                api_errors.addError('siren', 'Ce lieu ne peut enregistrer de SIRET car la structure associée n\'a pas de'
                                + 'SIREN renseigné')
            if self.siret is not None \
                    and managingOfferer is not None \
                    and not self.siret.startswith(managingOfferer.siren):
                api_errors.addError('siret', 'Le code SIRET doit correspondre à un établissement de votre structure')

        return api_errors

    @property
    def nOffers(self):
        return Offer.query.filter_by(venue=self).count()


@listens_for(Venue, 'before_insert')
def before_insert(mapper, connect, self):
    _check_if_existing_virtual_venue(self)
    _fill_department_code_from_postal_code(self)


@listens_for(Venue, 'before_update')
def before_update(mapper, connect, self):
    _check_if_existing_virtual_venue(self)
    _fill_department_code_from_postal_code(self)


def _check_if_existing_virtual_venue(self):
    if self.isVirtual:
        virtual_venues_count = Venue.query \
            .filter_by(managingOffererId=self.managingOffererId, isVirtual=True) \
            .count()
        if virtual_venues_count == 1:
            raise TooManyVirtualVenuesException()


def _fill_department_code_from_postal_code(self):
    if not self.isVirtual:
        if not self.postalCode:
            raise IntegrityError(None, None, None)
        self.store_department_code()


class TooManyVirtualVenuesException(Exception):
    pass


def create_digital_venue(offerer):
    digital_venue = Venue()
    digital_venue.isVirtual = True
    digital_venue.name = "Offre en ligne"
    digital_venue.managingOfferer = offerer
    return digital_venue


Venue.__ts_vector__ = create_tsvector(
    cast(coalesce(Venue.name, ''), TEXT),
    cast(coalesce(Venue.address, ''), TEXT),
    cast(coalesce(Venue.siret, ''), TEXT)
)

Venue.__table_args__ = (
    Index(
        'idx_venue_fts',
        Venue.__ts_vector__,
        postgresql_using='gin'
    ),
)

