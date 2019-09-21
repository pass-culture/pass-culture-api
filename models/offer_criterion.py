from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_api_handler import ApiHandler

from models.db import Model


class OfferCriterion(ApiHandler, Model):
    offerId = Column(BigInteger,
                     ForeignKey('offer.id'),
                     index=True,
                     nullable=False)

    offer = relationship('Offer',
                         foreign_keys=[offerId],
                         backref='offerCriteria')

    criterionId = Column(BigInteger,
                         ForeignKey('criterion.id'),
                         index=True,
                         nullable=False)

    criterion = relationship('Criterion',
                             foreign_keys=[criterionId],
                             backref='offerCriteria')
