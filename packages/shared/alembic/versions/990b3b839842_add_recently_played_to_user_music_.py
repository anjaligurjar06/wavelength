"""add recently played to user music profiles

Revision ID: 990b3b839842
Revises: 71d5b76866e8
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "990b3b839842"
down_revision: str | Sequence[str] | None = "71d5b76866e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_music_profiles",
        sa.Column(
            "recently_played",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "user_music_profiles",
        "recently_played",
    )