from alembic import context
from sqlalchemy import create_engine


# This order is needed to prevent circular dependency due to
# EducationalBooking needing db.Model needing Booking needing EducationalBooking.
# This is because we import every model in the models.__init.py__
# fmt: off
# isort: off
from pcapi.models.db import db
# isort: on
# fmt: on

from pcapi import settings
from pcapi.core.educational.models import EducationalDeposit  # pylint: disable=unused-import
from pcapi.core.educational.models import EducationalInstitution  # pylint: disable=unused-import
from pcapi.core.educational.models import EducationalYear  # pylint: disable=unused-import


target_metadata = db.metadata


def include_object(object, name, type_, reflected, compare_to) -> bool:  # pylint: disable=redefined-builtin
    # Don't generate DROP tables with autogenerate
    # https://alembic.sqlalchemy.org/en/latest/cookbook.html#don-t-generate-any-drop-table-directives-with-autogenerate
    if type_ == "table" and reflected and compare_to is None:
        return False
    if name in ("transaction", "activity"):
        return False
    return True


def run_migrations() -> None:
    db_options = []
    if settings.DB_MIGRATION_LOCK_TIMEOUT:
        db_options.append("-c lock_timeout=%i" % settings.DB_MIGRATION_LOCK_TIMEOUT)
    if settings.DB_MIGRATION_STATEMENT_TIMEOUT:
        db_options.append("-c statement_timeout=%i" % settings.DB_MIGRATION_STATEMENT_TIMEOUT)

    connectable = create_engine(settings.DATABASE_URL, connect_args={"options": " ".join(db_options)})

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            include_schemas=True,
            transaction_per_migration=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
