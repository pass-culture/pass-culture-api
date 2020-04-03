"""create_a_cancellation_date_on_booking

Revision ID: 5bccb7eb3d68
Revises: 85af82acac13
Create Date: 2020-03-31 08:13:48.720708

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bccb7eb3d68'
down_revision = '85af82acac13'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('booking', sa.Column('cancellationDate', sa.DateTime, nullable=True))
    op.execute("""
        BEGIN TRANSACTION;
            CREATE OR REPLACE FUNCTION save_cancellation_date()
            RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW."isCancelled" IS TRUE AND OLD."cancellationDate" IS NULL THEN
                        NEW."cancellationDate" = NOW();
                    ELSIF NEW."isCancelled" IS FALSE THEN
                        NEW."cancellationDate" = null;
                    END IF;
                    RETURN NEW;
                END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS stock_update_cancellation_date ON booking;

            CREATE TRIGGER stock_update_cancellation_date
            BEFORE INSERT OR UPDATE ON booking
            FOR EACH ROW
            EXECUTE PROCEDURE save_cancellation_date();
        COMMIT;
    """)


def downgrade():
    op.drop_column('booking', 'cancellationDate')
    op.execute("""
        BEGIN TRANSACTION;
            DROP TRIGGER IF EXISTS stock_update_cancellation_date ON booking;
            DROP FUNCTION IF EXISTS save_cancellation_date;
        COMMIT;
    """)
