""" event occurrence """
from sqlalchemy import Binary,\
                       BigInteger,\
                       Column,\
                       DateTime,\
                       Enum,\
                       ForeignKey
from sqlalchemy.orm import relationship

from models.db import Model
from models.event import EventType
from models.deactivable_mixin import DeactivableMixin
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin


class EventOccurrence(PcObject,
                      Model,
                      DeactivableMixin,
                      ProvidableMixin
                     ):

    id = Column(BigInteger,
                primary_key=True)

    type = Column(Enum(EventType),
                  nullable=True)

    offerId = Column(BigInteger,
                     ForeignKey('offer.id'),
                     index=True,
                     nullable=False)

    offer = relationship('Offer',
                         foreign_keys=[offerId],
                         backref='eventOccurrences')

    beginningDatetime = Column(DateTime,
                               index=True,
                               nullable=False)

    endDatetime = Column(DateTime,
                         nullable=False)

    accessibility = Column(Binary(1),
                           nullable=False,
                           default=bytes([0]))
