from sqlalchemy import Column, \
    String, Binary
from sqlalchemy_api_handler import ApiHandler

from models.db import Model


class PaymentMessage(ApiHandler, Model):
    name = Column(String(50), unique=True, nullable=False)

    checksum = Column(Binary(32), unique=True, nullable=False)
