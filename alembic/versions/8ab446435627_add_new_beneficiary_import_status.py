"""add_new_beneficiary_import_status

Revision ID: 8ab446435627
Revises: 5b12b14f1b17
Create Date: 2020-05-04 13:27:14.285474

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ab446435627'
down_revision = '5b12b14f1b17'
branch_labels = None
depends_on = None

previous_values = ('DUPLICATE', 'CREATED', 'ERROR', 'REJECTED', 'RETRY')
new_values = ('DUPLICATE', 'CREATED', 'ERROR', 'REJECTED', 'RETRY', 'PENDING')
previous_enum = sa.Enum(*previous_values, name='importstatus')
temporary_enum = sa.Enum(*new_values, name='tmp_importstatus')
new_enum = sa.Enum(*new_values, name='importstatus')


def upgrade():
    # Migration in 3 steps is required to match Postgres way of working
    temporary_enum.create(op.get_bind(), checkfirst=False)

    op.execute("""
        ALTER TABLE beneficiary_import_status
        ALTER COLUMN status
        TYPE tmp_importstatus
        USING status::text::tmp_importstatus
        """)

    # Remove unused old type
    previous_enum.drop(op.get_bind(), checkfirst=False)

    # Create the new one
    new_enum.create(op.get_bind(), checkfirst=False)

    op.execute("""
        ALTER TABLE beneficiary_import_status
        ALTER COLUMN status
        TYPE importstatus
        USING status::text::importstatus
        """)

    # Remove temporary type
    temporary_enum.drop(op.get_bind(), checkfirst=False)


def downgrade():
    temporary_enum.create(op.get_bind(), checkfirst=False)
    op.execute("""
            ALTER TABLE beneficiary_import_status
            ALTER COLUMN status
            TYPE tmp_importstatus
            USING status::text::tmp_importstatus
            """)

    new_enum.drop(op.get_bind(), checkfirst=False)

    previous_enum.create(op.get_bind(), checkfirst=False)

    op.execute("""
            ALTER TABLE beneficiary_import_status
            ALTER COLUMN status
            TYPE importstatus
            USING status::text::importstatus
            """)
    temporary_enum.drop(op.get_bind(), checkfirst=False)

