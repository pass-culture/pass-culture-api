from sqlalchemy import Column, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy_api_handler import ApiHandler

from models.db import Model

class Favorite(ApiHandler, Model):
    userId = Column(BigInteger,
                    ForeignKey("user.id"),
                    index=True,
                    nullable=False)

    user = relationship('User',
                        foreign_keys=[userId],
                        backref='favorites')

    offerId = Column(BigInteger,
                     ForeignKey("offer.id"),
                     index=True,
                     nullable=False)

    offer = relationship('Offer',
                         foreign_keys=[offerId],
                         backref='favorites')

    mediationId = Column(BigInteger,
                         ForeignKey("mediation.id"),
                         index=True,
                         nullable=True)

    mediation = relationship('Mediation',
                             foreign_keys=[mediationId],
                             backref='favorites')

    __table_args__ = (
        UniqueConstraint(
            'userId',
            'offerId',
            name='unique_favorite',
        ),
    )

    @property
    def thumbUrl(self):
        if self.mediationId:
            return self.mediation.thumbUrl

        if self.offer.product.thumbCount:
            return self.offer.product.thumbUrl
