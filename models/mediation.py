""" mediation model """
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, \
    BigInteger, \
    CheckConstraint, \
    DateTime, \
    ForeignKey, \
    Integer, \
    Text, \
    String
from sqlalchemy.orm import relationship

from models import DeactivableMixin
from models.has_thumb_mixin import HasThumbMixin
from models.pc_object import PcObject
from models.providable_mixin import ProvidableMixin


class Mediation(PcObject,
                HasThumbMixin,
                ProvidableMixin,
                DeactivableMixin):

    id = Column(BigInteger,
                primary_key=True,
                autoincrement=True)

    frontText = Column(Text, nullable=True)

    backText = Column(Text, nullable=True)

    credit = Column(String(255), nullable=True)

    dateCreated = Column(DateTime,
                         nullable=False,
                         default=datetime.utcnow)

    authorId = Column(BigInteger,
                      ForeignKey("user.id"),
                      nullable=True)

    author = relationship('User',
                          foreign_keys=[authorId],
                          backref='mediations')

    offerId = Column(BigInteger,
                     ForeignKey('offer.id'),
                     index=True,
                     nullable=True)

    offer = relationship('Offer',
                         foreign_keys=[offerId],
                         backref='mediations')

    tutoIndex = Column(Integer,
                       nullable=True,
                       index=True)


Mediation.__table_args__ = (
    CheckConstraint('"thumbCount" <= 2',
                    name='check_mediation_has_max_2_thumbs'),
    CheckConstraint('"thumbCount" > 0 OR frontText IS NOT NULL',
                    name='check_mediation_has_thumb_or_text'),
    CheckConstraint('("offerId" IS NOT NULL AND "tutoIndex" IS NULL)'
                    + ' OR ("offerId" IS NULL AND "tutoIndex" IS NOT NULL)',
                    name='check_mediation_has_offer_xor_tutoIndex'),
)


TUTOS_PATH = Path(os.path.dirname(os.path.realpath(__file__))) / '..'\
                 / 'static' / 'tuto_mediations'


def upsertTutoMediation(index, has_back=False):
    existing_mediation = Mediation.query.filter_by(tutoIndex=index)\
                                        .first()
    mediation = existing_mediation or Mediation()
    mediation.tutoIndex = index
    PcObject.save(mediation)

    with open(TUTOS_PATH / (str(index) + '.png'), "rb") as f:
        mediation.save_thumb(f.read(),
                             0,
                             convert=False,
                             image_type='png')

    if has_back:
        with open(TUTOS_PATH / (str(index) + '_verso.png'), "rb") as f:
            mediation.save_thumb(f.read(),
                                 1,
                                 convert=False,
                                 image_type='png')

    PcObject.save(mediation)


def upsertTutoMediations():
    upsertTutoMediation(0)
    upsertTutoMediation(1, True)
