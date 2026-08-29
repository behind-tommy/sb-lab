"""create notes table

Revision ID: 49f1e088d24e
Revises:
Create Date: 2026-08-29 14:55:06.145874

This file is a "migration" — a single, tracked, reversible change to the
database's schema (its table structure). Alembic keeps a record of which
migrations have already run on a given database, and runs any new ones in
order (`alembic upgrade head`) — so the schema always matches the code,
without anyone hand-editing tables directly.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '49f1e088d24e'
down_revision: str | Sequence[str] | None = None  # None = this is the first migration ever
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration: create the notes table."""
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Undo this migration: delete the notes table (and all its data!)."""
    op.drop_table("notes")
