import enum

from sqlalchemy import String, Column, Enum

from models.db import Model
from models.deactivable_mixin import DeactivableMixin
from models.pc_object import PcObject


class FeatureToggle(enum.Enum):
    WEBAPP_SIGNUP = 'Permettre aux bénéficiaires de créer un compte'
    DEGRESSIVE_REIMBURSEMENT_RATE = 'Permettre le remboursement avec un barème dégressif par lieu'
    DUO_OFFER = 'Permettre la réservation d’une offre pour soi et un accompagnant'
    QR_CODE = 'Permettre la validation d''une contremarque via QR code'


class Feature(PcObject, Model, DeactivableMixin):
    name = Column(Enum(FeatureToggle), index=True, unique=True, nullable=False)
    description = Column(String(300), nullable=False)

    @property
    def nameKey(self):
        return str(self.name).replace('FeatureToggle.', '')
