
"""add GIN index for chunk lexical search

Revision ID: 3236f5a3924c
"""

from alembic import op

revision = "3236f5a3924c"
down_revision = "920105962f92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX chunks_text_search_gin_idx
        ON chunks
        USING GIN (to_tsvector('english', text))
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS chunks_text_search_gin_idx
    """)
