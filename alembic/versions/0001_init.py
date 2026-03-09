"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_resources_name", "resources", ["name"], unique=True)

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.CheckConstraint("end_at > start_at", name="ck_reservation_time_range"),
        sa.UniqueConstraint("resource_id", "start_at", "end_at", name="uq_reservation_exact_slot"),
    )
    op.create_index("ix_reservations_lookup", "reservations", ["resource_id", "status", "start_at", "end_at"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=100), nullable=False),
        sa.Column("detail", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_reservations_lookup", table_name="reservations")
    op.drop_table("reservations")
    op.drop_index("ix_resources_name", table_name="resources")
    op.drop_table("resources")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
