from domain.offerer.offerer_repository import OffererRepository
from domain.offerer.offerer import Offerer
from infrastructure.repository.offerer import offerer_domain_converter
from models import Offerer as OffererSQLEntity


class OffererSQLRepository(OffererRepository):
    def find_by_siren(self, siren: str) -> Offerer:

        offerer_sql_entity: OffererSQLEntity = OffererSQLEntity.query.filter_by(siren=siren).first()

        if offerer_sql_entity is not None:
            return offerer_domain_converter.to_domain(offerer_sql_entity)
