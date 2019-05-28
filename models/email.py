import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, Enum

from models.pc_object import PcObject


class EmailStatus(enum.Enum):
    SENT = 'SENT'
    ERROR = 'ERROR'


class Email(PcObject):
    content = Column(JSON,
                     nullable=False)
    status = Column(Enum(EmailStatus),
                    nullable=False,
                    index=True)

    datetime = Column(DateTime,
                      nullable=False,
                      default=datetime.utcnow)
