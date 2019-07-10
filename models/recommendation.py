""" recommendation model """
from datetime import datetime

from sqlalchemy import BigInteger, \
    Boolean, \
    Column, \
    DateTime, \
    ForeignKey, \
    String, \
    and_, \
    exists
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import expression, select

from models import Favorite
from models.db import Model
from models.pc_object import PcObject


class Recommendation(PcObject, Model):
    id = Column(BigInteger,
                primary_key=True,
                autoincrement=True)

    userId = Column(BigInteger,
                    ForeignKey('user.id'),
                    nullable=False,
                    index=True)

    user = relationship('User',
                        foreign_keys=[userId],
                        backref='recommendations')

    mediationId = Column(BigInteger,
                         ForeignKey('mediation.id'),
                         index=True,
                         nullable=True)  # NULL for recommendation created directly from a thing or an event

    mediation = relationship('Mediation',
                             foreign_keys=[mediationId],
                             backref='recommendations')

    offerId = Column(BigInteger,
                     ForeignKey('offer.id'),
                     index=True,
                     nullable=True)

    offer = relationship('Offer',
                         foreign_keys=[offerId],
                         backref='recommendations')

    shareMedium = Column(String(20),
                         nullable=True)

    dateCreated = Column(DateTime,
                         nullable=False,
                         default=datetime.utcnow)

    dateUpdated = Column(DateTime,
                         nullable=False,
                         default=datetime.utcnow)

    dateRead = Column(DateTime,
                      nullable=True,
                      index=True)

    validUntilDate = Column(DateTime,
                            nullable=True,
                            index=True)

    isClicked = Column(Boolean,
                       nullable=False,
                       server_default=expression.false(),
                       default=False)

    isFirst = Column(Boolean,
                     nullable=False,
                     server_default=expression.false(),
                     default=False)

    search = Column(String,
                    nullable=True)

    isFavorite = column_property(
        exists(select([Favorite.id]).
               where(and_(userId == Favorite.userId,
                          (offerId == Favorite.offerId))
                     )
               ))

    @property
    def thumbUrl(self):
        if self.mediationId:
            return self.mediation.thumbUrl

        return self.offer.product.thumbUrl
