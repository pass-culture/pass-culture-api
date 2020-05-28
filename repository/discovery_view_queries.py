from sqlalchemy_utils import refresh_materialized_view

from models import DiscoveryView
from models.db import db


def refresh(concurrently: bool = True) -> None:
    refresh_materialized_view(db.session, DiscoveryView.__tablename__, concurrently)
    db.session.commit()
