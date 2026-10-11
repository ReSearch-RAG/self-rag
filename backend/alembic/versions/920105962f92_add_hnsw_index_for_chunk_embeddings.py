"""add HNSW index for chunk embeddings

Revision ID: 920105962f92
Revises: c2d94e9d29e2
Create Date: 2026-10-11 22:55:14.092552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '920105962f92'
down_revision: Union[str, Sequence[str], None] = 'c2d94e9d29e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX chunks_embedding_hnsw_idx
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS chunks_embedding_hnsw_idx
    """)