"""add wellbeing_card_selections table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'wellbeing_card_selections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('selection_date', sa.Date(), nullable=False),
        sa.Column('card_ids', sa.JSON(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'selection_date', name='uq_wellbeing_selection_date'),
    )
    op.create_index(op.f('ix_wellbeing_card_selections_user_id'), 'wellbeing_card_selections', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_wellbeing_card_selections_user_id'), table_name='wellbeing_card_selections')
    op.drop_table('wellbeing_card_selections')
