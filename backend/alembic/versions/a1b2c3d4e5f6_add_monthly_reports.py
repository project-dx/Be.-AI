"""add monthly_reports table

Revision ID: a1b2c3d4e5f6
Revises: 80ac12bd5c83
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '80ac12bd5c83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'monthly_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('model_name', sa.String(length=50), nullable=False),
        sa.Column('prompt_version', sa.String(length=10), nullable=False),
        sa.Column('facts_json', sa.JSON(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_monthly_reports_year_month'), 'monthly_reports', ['year_month'], unique=False)
    op.create_index(op.f('ix_monthly_reports_created_at'), 'monthly_reports', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_monthly_reports_created_at'), table_name='monthly_reports')
    op.drop_index(op.f('ix_monthly_reports_year_month'), table_name='monthly_reports')
    op.drop_table('monthly_reports')
