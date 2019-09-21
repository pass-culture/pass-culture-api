import enum
from sqlalchemy import BigInteger, Column, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy_api_handler import ApiHandler

from models.db import Model
from models.needs_validation_mixin import NeedsValidationMixin


class RightsType(enum.Enum):
    admin = "admin"
    editor = "editor"


class UserOfferer(ApiHandler, Model, NeedsValidationMixin):

    userId = Column(BigInteger,
                    ForeignKey('user.id'),
                    primary_key=True)

    user = relationship('User',
                        foreign_keys=[userId],
                        backref=backref("UserOfferers"))

    offererId = Column(BigInteger,
                       ForeignKey('offerer.id'),
                       index=True,
                       primary_key=True)

    offerer = relationship('Offerer',
                           foreign_keys=[offererId],
                           backref=backref("UserOfferers"))

    rights = Column(Enum(RightsType))

    __table_args__ = (
        UniqueConstraint(
            'userId',
            'offererId',
            name='unique_user_offerer',
            ),
        )
