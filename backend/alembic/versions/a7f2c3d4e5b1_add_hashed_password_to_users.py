"""add hashed_password to users

Revision ID: a7f2c3d4e5b1
Revises: c2d94e9d29e2
Create Date: 2026-11-18 00:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7f2c3d4e5b1"
down_revision: str = "c2d94e9d29e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the column as nullable first so existing rows are not rejected
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(), nullable=True),
    )
    # Set a placeholder hash for any existing rows (bcrypt hash of "changeme")
    op.execute(
        "UPDATE users SET hashed_password = "
        "'$2b$12$placeholder000000000000000000000000000000000000000' "
        "WHERE hashed_password IS NULL"
    )
    # Now make the column non-nullable
    op.alter_column(
        "users",
        "hashed_password",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
