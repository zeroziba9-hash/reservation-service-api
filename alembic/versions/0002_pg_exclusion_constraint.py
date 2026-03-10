"""add postgres exclusion constraint for reservation overlap safety

Revision ID: 0002_pg_exclusion_constraint
Revises: 0001_init
Create Date: 2026-03-10
"""

from alembic import op

revision = "0002_pg_exclusion_constraint"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("""
        ALTER TABLE reservations
        ADD CONSTRAINT ex_reservations_no_overlap
        EXCLUDE USING gist (
          resource_id WITH =,
          tsrange(start_at, end_at, '[)') WITH &&
        )
        WHERE (status = 'BOOKED')
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("""
        ALTER TABLE reservations
        DROP CONSTRAINT IF EXISTS ex_reservations_no_overlap
        """)
