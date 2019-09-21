from sqlalchemy import Column, String, Text, Integer
from sqlalchemy_api_handler import ApiHandler

from models.db import Model


class Criterion(ApiHandler, Model):
    name = Column(String(140), nullable=False)

    description = Column(Text, nullable=True)

    scoreDelta = Column(Integer, nullable=False)

    def __repr__(self):
        return '%s' % self.name
