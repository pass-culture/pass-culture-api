""" event occurrence """
from datetime import datetime
from sqlalchemy import Binary, BigInteger, Column, DateTime, Enum, \
    ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from models.db import Model
from models.event import EventType
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin
from models.soft_deletable_mixin import SoftDeletableMixin


class EventOccurrence(PcObject,
                      Model,
                      ProvidableMixin,
                      SoftDeletableMixin):

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
                         CheckConstraint('"endDatetime" > "beginningDatetime"',
                                         name='check_end_datetime_is_after_beginning_datetime'),
                         nullable=False)

    accessibility = Column(Binary(1),
                           nullable=False,
                           default=bytes([0]))

    def errors(self):
        api_errors = super(EventOccurrence, self).errors()

        error_key = 'global'

        beginning_datetime = self.beginningDatetime
        if type(beginning_datetime) == str:
            beginning_datetime = datetime.strptime(beginning_datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
            error_key = 'beginningDatetime'

        end_datetime = self.endDatetime
        if type(end_datetime) == str:
            end_datetime = datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
            error_key = 'endDatetime'

        if beginning_datetime > end_datetime:
            api_errors.addError(error_key, 'La date de fin de l\'événement doit être postérieure à la date de début')

        return api_errors
