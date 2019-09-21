import enum
from sqlalchemy import String, Column, Enum
from sqlalchemy_api_handler import ApiHandler

from models.db import Model
from models.deactivable_mixin import DeactivableMixin


class FeatureToggle(enum.Enum):
    WEBAPP_SIGNUP = 'Permettre aux bénéficiaires de créer un compte'
    FAVORITE_OFFER = 'Permettre aux bénéficiaires d''ajouter des offres en favoris'
    DEGRESSIVE_REIMBURSEMENT_RATE = 'Permettre le remboursement avec un barème dégressif par lieu'


class Feature(ApiHandler, Model, DeactivableMixin):
    name = Column(Enum(FeatureToggle), unique=True, nullable=False)
    description = Column(String(300), nullable=False)

    @property
    def nameKey(self):
        return str(self.name).replace('FeatureToggle.', '')
