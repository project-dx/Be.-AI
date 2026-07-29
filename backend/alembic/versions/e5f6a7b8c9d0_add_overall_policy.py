"""add overall_policy to support_plans

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('support_plans') as batch:
        batch.add_column(sa.Column('overall_policy', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('support_plans') as batch:
        batch.drop_column('overall_policy')
