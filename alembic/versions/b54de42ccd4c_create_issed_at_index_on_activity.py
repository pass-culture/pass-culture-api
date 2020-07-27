"""create_issed_at_index_on_activity

Revision ID: b54de42ccd4c
Revises: e52827be0601
Create Date: 2020-07-27 13:01:25.768342

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b54de42ccd4c'
down_revision = 'e52827be0601'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("COMMIT;")
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_issed_at ON activity(issued_at);")


def downgrade() -> None:
    pass
