"""add unique constraint on source_url and chunk_index

Revision ID: 9f2c8e7b43a6
Revises: b05aa88c6447
Create Date: 2026-06-14 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9f2c8e7b43a6'
down_revision: Union[str, Sequence[str], None] = 'b05aa88c6447'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_document_chunk_source_url_chunk_index',
        'document_chunk',
        ['source_url', 'chunk_index'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_document_chunk_source_url_chunk_index',
        'document_chunk',
    )
