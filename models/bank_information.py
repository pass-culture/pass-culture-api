from sqlalchemy import Column, BigInteger, ForeignKey, String, Integer, Enum
from sqlalchemy.orm import relationship, backref
import enum

from models.db import Model
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin
from models.versioned_mixin import VersionedMixin


class BankInformationStatus(enum.Enum):
    REJECTED = "REJECTED"
    DRAFT = "DRAFT"
    ACCEPTED = "ACCEPTED"


class BankInformation(PcObject, Model, ProvidableMixin, VersionedMixin):
    offererId = Column(BigInteger,
                       ForeignKey("offerer.id"),
                       index=True,
                       nullable=True,
                       unique=True)

    offerer = relationship('Offerer',
                           foreign_keys=[offererId],
                           backref=backref('bankInformation', uselist=False))

    venueId = Column(BigInteger,
                     ForeignKey("venue.id"),
                     index=True,
                     nullable=True,
                     unique=True)

    venue = relationship('Venue',
                         foreign_keys=[venueId],
                         backref=backref('bankInformation', uselist=False))

    iban = Column(String(27),
                  nullable=True)

    bic = Column(String(11),
                 nullable=True)

    applicationId = Column(Integer,
                           nullable=False)

    status = Column(Enum(BankInformationStatus), nullable=False)
