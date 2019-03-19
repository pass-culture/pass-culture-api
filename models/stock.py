""" stock """
from datetime import datetime, timedelta
from sqlalchemy import BigInteger, \
                       CheckConstraint, \
                       Column, \
                       DateTime, \
                       DDL, \
                       event, \
                       ForeignKey, \
                       Integer, \
                       Numeric
from sqlalchemy.orm import relationship

from models.versioned_mixin import VersionedMixin
from models.db import Model
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin
from models.soft_deletable_mixin import SoftDeletableMixin


class Stock(PcObject,
            Model,
            ProvidableMixin,
            SoftDeletableMixin,
            VersionedMixin):

    dateModified = Column(DateTime,
                          nullable=False,
                          default=datetime.utcnow)

    beginningDatetime = Column(DateTime,
                               index=True,
                               nullable=True)

    endDatetime = Column(DateTime,
                         CheckConstraint('"endDatetime" > "beginningDatetime"',
                                         name='check_end_datetime_is_after_beginning_datetime'),
                         nullable=True)

    offerId = Column(BigInteger,
                     ForeignKey('offer.id'),
                     index=True,
                     nullable=True)

    offer = relationship('Offer',
                         foreign_keys=[offerId],
                         backref='stocks')


    price = Column(Numeric(10, 2),
                   CheckConstraint('price >= 0', name='check_price_is_not_negative'),
                   nullable=False)

    available = Column(Integer,
                       index=True,
                       nullable=True)

    # TODO: add pmr
    #pmrGroupSize = Column(db.Integer,
    #                         nullable=False,
    #                         default=1)

    groupSize = Column(Integer,
                       nullable=False,
                       default=1)

    bookingLimitDatetime = Column(DateTime,
                                  nullable=True)

    bookingRecapSent = Column(DateTime,
                              nullable=True)

    def errors(self):
        api_errors = super(Stock, self).errors()
        if self.endDatetime \
           and self.beginningDatetime \
           and self.endDatetime < self.beginningDatetime:
            api_errors.addError('endDatetime', 'La date de fin de l\'événement doit être postérieure à la date de début')
        return api_errors

    @property
    def resolvedOffer(self):
        return self.offer or self.eventOccurrence.offer

    def queryNotSoftDeleted():
        return Stock.query.filter_by(isSoftDeleted=False)


@event.listens_for(Stock, 'before_insert')
def page_defaults(mapper, configuration, target):
    # `bookingLimitDatetime` defaults to midnight before `beginningDatetime`
    # for eventOccurrences
    if target.beginningDatetime and not target.bookingLimitDatetime:
        target.bookingLimitDatetime = target.beginningDatetime\
                                            .replace(hour=23)\
                                            .replace(minute=59) - timedelta(days=3)


Stock.trig_ddl = """
    CREATE OR REPLACE FUNCTION check_stock()
    RETURNS TRIGGER AS $$
    BEGIN
      IF NOT NEW.available IS NULL AND
      ((SELECT COUNT(*) FROM booking WHERE "stockId"=NEW.id) > NEW.available) THEN
        RAISE EXCEPTION 'available_too_low'
              USING HINT = 'stock.available cannot be lower than number of bookings';
      END IF;

      IF NOT NEW."bookingLimitDatetime" IS NULL AND
         NOT NEW."beginningDatetime" IS NULL AND
         NEW."bookingLimitDatetime" > NEW."beginningDatetime" THEN

      RAISE EXCEPTION 'bookingLimitDatetime_too_late'
      USING HINT = 'bookingLimitDatetime after beginningDatetime';
      END IF;

      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS stock_update ON stock;
    CREATE CONSTRAINT TRIGGER stock_update AFTER INSERT OR UPDATE
    ON stock
    FOR EACH ROW EXECUTE PROCEDURE check_stock()
    """
event.listen(Stock.__table__,
             'after_create',
             DDL(Stock.trig_ddl))
