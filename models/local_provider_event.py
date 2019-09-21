import enum
from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy_api_handler import ApiHandler

from models.db import Model


class LocalProviderEventType(enum.Enum):
    SyncError = "SyncError"

    SyncPartStart = "SyncPartStart"
    SyncPartEnd = "SyncPartEnd"

    SyncStart = "SyncStart"
    SyncEnd = "SyncEnd"


class LocalProviderEvent(ApiHandler, Model):

    id = Column(BigInteger,
                primary_key=True,
                autoincrement=True)

    providerId = Column(BigInteger,
                        ForeignKey("provider.id"),
                        nullable=False)

    provider = relationship('Provider',
                            foreign_keys=[providerId])

    date = Column(DateTime,
                  nullable=False,
                  default=datetime.utcnow)

    type = Column(Enum(LocalProviderEventType),
                  nullable=False)

    payload = Column(String(50),
                     nullable=True)
