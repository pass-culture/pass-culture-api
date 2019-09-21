import enum
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, Enum
from sqlalchemy_api_handler import ApiHandler

from models.db import Model


class EmailStatus(enum.Enum):
    SENT = 'SENT'
    ERROR = 'ERROR'


class Email(ApiHandler, Model):
    content = Column(JSON,
                     nullable=False)
    status = Column(Enum(EmailStatus),
                    nullable=False,
                    index=True)

    datetime = Column(DateTime,
                      nullable=False,
                      default=datetime.utcnow)
