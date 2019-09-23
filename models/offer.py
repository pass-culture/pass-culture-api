from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, desc, ForeignKey, String
from sqlalchemy import and_, ARRAY, Boolean, CheckConstraint, false, Integer, Text, TEXT
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import select, func

from domain.keywords import create_ts_vector_and_table_args
from models import ExtraDataMixin
from models.criterion import Criterion
from models.db import db, Model
from models.deactivable_mixin import DeactivableMixin
from models.offer_criterion import OfferCriterion
from models.offer_type import ThingType, EventType, ProductType
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin
from models.stock import Stock
from models.venue import Venue
from utils.date import DateTimes
from utils.inflect_engine import pluralize

class Offer(PcObject,
            Model,
            ExtraDataMixin,
            DeactivableMixin,
            ProvidableMixin):
    # We redefine this so we can reference it in the baseScore column_property
    id = Column(BigInteger,
                primary_key=True,
                autoincrement=True)

    productId = Column(BigInteger,
                       ForeignKey("product.id"),
                       index=True,
                       nullable=False)

    product = relationship('Product',
                           foreign_keys=[productId],
                           backref='offers')

    venueId = Column(BigInteger,
                     ForeignKey("venue.id"),
                     nullable=False,
                     index=True)

    venue = relationship('Venue',
                         foreign_keys=[venueId],
                         backref='offers')

    bookingEmail = Column(String(120), nullable=True)

    type = Column(String(50),
                  CheckConstraint("type != 'None'"),
                  index=True,
                  nullable=False)

    name = Column(String(140), nullable=False)

    description = Column(Text, nullable=True)

    conditions = Column(String(120),
                        nullable=True)

    ageMin = Column(Integer,
                    nullable=True)
    ageMax = Column(Integer,
                    nullable=True)

    url = Column(String(255), nullable=True)

    mediaUrls = Column(ARRAY(String(220)),
                       nullable=False,
                       default=[])

    durationMinutes = Column(Integer, nullable=True)

    isNational = Column(Boolean,
                        server_default=false(),
                        default=False,
                        nullable=False)

    dateCreated = Column(DateTime,
                         nullable=False,
                         default=datetime.utcnow)

    baseScore = column_property(
        select([func.coalesce(func.sum(Criterion.scoreDelta), 0)]).
            where(and_(Criterion.id == OfferCriterion.criterionId,
                       (OfferCriterion.offerId == id))
                  )
    )

    criteria = relationship('Criterion',
                            backref=db.backref('criteria', lazy='dynamic'),
                            secondary='offer_criterion')

    def errors(self):
        api_errors = super(Offer, self).errors()
        if self.venue:
            venue = self.venue
        else:
            venue = Venue.query.get(self.venueId)
        if self.isDigital and not venue.isVirtual:
            api_errors.add_error('venue',
                                 'Une offre numérique doit obligatoirement être associée au lieu "Offre numérique"')
        elif not self.isDigital and venue.isVirtual:
            api_errors.add_error('venue', 'Une offre physique ne peut être associée au lieu "Offre numérique"')
        if self.isDigital and self._type_can_only_be_offline():
            api_errors.add_error('url', 'Une offre de type {} ne peut pas être numérique'.format(
                self._get_label_from_type_string()))

        return api_errors

    def update_with_product_data(self, product_dict: dict):
        owning_offerer = self.product.owningOfferer
        if owning_offerer and owning_offerer == self.venue.managingOfferer:
            self.product.populate_from_dict(product_dict)

    @property
    def activeMediation(self):
        sorted_by_date_desc = sorted(self.mediations, key=lambda m: m.dateCreated, reverse=True)
        only_active = list(filter(lambda m: m.isActive, sorted_by_date_desc))
        return only_active[0] if only_active else None

    @property
    def dateRange(self):
        if ProductType.is_thing(self.type) or not self.notDeletedStocks:
            return DateTimes()

        start = min([stock.beginningDatetime for stock in self.notDeletedStocks])
        end = max([stock.endDatetime for stock in self.notDeletedStocks])
        return DateTimes(start, end)

    @property
    def hasActiveMediation(self):
        return any(map(lambda m: m.isActive, self.mediations))

    @property
    def isEvent(self):
        return ProductType.is_event(self.type)

    @property
    def isThing(self):
        return ProductType.is_thing(self.type)

    @property
    def isDigital(self):
        return self.url is not None and self.url != ''

    @property
    def isEditable(self):
        return self.lastProviderId is None

    @property
    def isFinished(self):
        return all(map(lambda s: not s.isBookable, self.stocks))

    @property
    def isFullyBooked(self):
        if self._has_unlimited_stock():
            return False

        bookable_stocks = list(filter(lambda s: s.isBookable, self.stocks))
        total_quantity = 0

        for stock in bookable_stocks:
            bookings = filter(lambda b: not b.isCancelled and (b.dateUsed and b.dateUsed >= stock.dateModified), stock.bookings)
            total_quantity += sum(map(lambda s: s.quantity, bookings))

        available_stocks = sum(map(lambda s: s.available if s.isBookable else 0, self.stocks))
        return total_quantity >= available_stocks

    @property
    def lastStock(self):
        query = Stock.queryNotSoftDeleted()
        return query.join(Offer) \
            .filter(Offer.id == self.id) \
            .order_by(desc(Stock.bookingLimitDatetime)) \
            .first()

    @property
    def notDeletedStocks(self):
        return [stock for stock in self.stocks if not stock.isSoftDeleted]

    @property
    def offerType(self):
        all_types = list(ThingType) + list(EventType)
        for possible_type in all_types:
            if str(possible_type) == self.type:
                return possible_type.as_dict()

    @property
    def stockAlertMessage(self) -> str:
        non_deleted_stocks = [stock for stock in self.stocks if not stock.isSoftDeleted]
        total_number_stocks = len(non_deleted_stocks)
        number_of_empty_stocks = len(
            list(filter(lambda s: s.available == 0 or s.remainingQuantity == 0, non_deleted_stocks)))
        remaining_for_all_stocks = sum(
            map(lambda s: s.remainingQuantity, filter(lambda s: s.available, non_deleted_stocks)))

        if total_number_stocks == 0:
            return 'pas encore de stock' if self.isThing else 'pas encore de places'

        if all([s.available is None for s in non_deleted_stocks]):
            return 'illimité'

        if self.isFullyBooked:
            return 'plus de stock' if self.isThing else 'plus de places pour toutes les dates'

        if number_of_empty_stocks >= 1:
            offer_word = pluralize(number_of_empty_stocks, 'offre')
            stock_or_place = 'stock' if self.isThing else 'places'
            return f'plus de {stock_or_place} pour {number_of_empty_stocks} {offer_word}'

        if not self.isFullyBooked:
            remaining_stock_word = 'en stock' if self.isThing else pluralize(remaining_for_all_stocks, 'place')
            return f'encore {remaining_for_all_stocks} {remaining_stock_word}'

    def _has_unlimited_stock(self):
        return any(map(lambda s: s.available is None, self.stocks))

    def _type_can_only_be_offline(self):
        offline_only_things = filter(lambda thing_type: thing_type.value['offlineOnly'], ThingType)
        offline_only_types_for_things = map(lambda x: x.__str__(), offline_only_things)
        return self.type in offline_only_types_for_things

    def _get_label_from_type_string(self):
        matching_type_thing = next(filter(lambda thing_type: str(thing_type) == self.type, ThingType))
        return matching_type_thing.value['proLabel']


ts_indexes = [('idx_offer_fts_name', Offer.name),
              ('idx_offer_fts_author', Offer.extraData['author'].cast(TEXT)),
              ('idx_offer_fts_byArtist', Offer.extraData['byArtist'].cast(TEXT)),
              ('idx_offer_fts_description', Offer.description)]

(Offer.__ts_vectors__, Offer.__table_args__) = create_ts_vector_and_table_args(ts_indexes)
