from typing import List

from models import Mediation


def find_by_id(mediation_id: str) -> Mediation:
    return Mediation.query.filter_by(id=mediation_id).first()


def get_all_tuto_mediations() -> List[Mediation]:
    return Mediation.query.filter(Mediation.tutoIndex != None) \
                          .order_by(Mediation.tutoIndex) \
                          .all()
