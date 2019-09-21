from datetime import datetime
from sqlalchemy import Column, BigInteger, Numeric, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy_api_handler import ApiHandler

from models.db import Model



class Deposit(ApiHandler, Model):
    id = Column(BigInteger,
                primary_key=True,
                autoincrement=True)

    amount = Column(Numeric(10, 2),
                    nullable=False)

    userId = Column(BigInteger,
                    ForeignKey('user.id'),
                    index=True,
                    nullable=False)

    user = relationship('User',
                        foreign_keys=[userId],
                        backref='deposits')

    source = Column(String(300),
                    nullable=False)

    dateCreated = Column(DateTime,
                         nullable=False,
                         default=datetime.utcnow)
