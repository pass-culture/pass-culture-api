from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from pcapi.models.db import Model
from pcapi.models.pc_object import PcObject


class OfferViewModel(PcObject, Model):
    __tablename__ = "offer_view_model"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    isActive = Column(Boolean, nullable=False)
    isEditable = Column(Boolean, nullable=False)
    hasBookingLimitDatetimesPassed = Column(Boolean, nullable=False)
    isEvent = Column(Boolean, index=True, nullable=False)
    isThing = Column(Boolean, index=True, nullable=False)

    remainingStockQuantity = Column(String(50), nullable=False)
    stocksCount = Column(Integer, nullable=False)
    soldOutStocksCount = Column(Integer, nullable=False)
    firstEventDatetime = Column(DateTime, index=True, nullable=True)
    lastEventDatetime = Column(DateTime, index=True, nullable=True)

    name = Column(String(140), nullable=False)
    thumbUrl = Column(String(255), nullable=True)
    status = Column(String(50), index=True, nullable=False)
    type = Column(String(50), index=True, nullable=False)
    creationMode = Column(String(50), index=True, nullable=False)
    timezone = Column(String(50), nullable=False)

    venueId = Column(BigInteger, nullable=False, index=True)
    venueName = Column(String(140), nullable=False)
    venueTimezone = Column(String(140), nullable=False)
    venuePublicName = Column(String(255), nullable=True)
    venueDepartementCode = Column(String(3), nullable=True)
    venueIsVirtual = Column(Boolean, nullable=False, default=False)

    offererId = Column(BigInteger, nullable=False, index=True)
    offererName = Column(String(140), nullable=False)
