"""add assessments, colorful_pyramids, monitoring_evaluations and vital columns

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 日報のバイタルデータ ---
    with op.batch_alter_table('user_daily_reports') as batch:
        batch.add_column(sa.Column('body_temperature', sa.Float(), nullable=True))
        batch.add_column(sa.Column('systolic_bp', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('diastolic_bp', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('pulse', sa.Integer(), nullable=True))

    # --- 初期アセスメント ---
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('life_history', sa.Text(), nullable=True),
        sa.Column('disability_characteristics', sa.Text(), nullable=True),
        sa.Column('thinking_style', sa.Text(), nullable=True),
        sa.Column('herrmann_a', sa.Integer(), nullable=True),
        sa.Column('herrmann_b', sa.Integer(), nullable=True),
        sa.Column('herrmann_c', sa.Integer(), nullable=True),
        sa.Column('herrmann_d', sa.Integer(), nullable=True),
        sa.Column('personal_values', sa.Text(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('support_needs', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_assessments_user_id'), 'assessments', ['user_id'], unique=True)

    # --- カラフルピラミッド ---
    op.create_table(
        'colorful_pyramids',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('wellbeing', sa.Text(), nullable=True),
        sa.Column('passion', sa.Text(), nullable=True),
        sa.Column('vision', sa.Text(), nullable=True),
        sa.Column('mission', sa.Text(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_colorful_pyramids_user_id'), 'colorful_pyramids', ['user_id'], unique=True)

    # --- 6か月モニタリング評価 ---
    op.create_table(
        'monitoring_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('support_plan_id', sa.Integer(), nullable=True),
        sa.Column('evaluation_date', sa.Date(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('score_summary_json', sa.JSON(), nullable=True),
        sa.Column('achievements', sa.Text(), nullable=True),
        sa.Column('challenges', sa.Text(), nullable=True),
        sa.Column('plan_adjustments', sa.Text(), nullable=True),
        sa.Column('next_period_focus', sa.Text(), nullable=True),
        sa.Column('staff_comment', sa.Text(), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=False),
        sa.Column('model_name', sa.String(length=50), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['support_plan_id'], ['support_plans.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_monitoring_evaluations_user_id'), 'monitoring_evaluations', ['user_id'], unique=False)
    op.create_index(op.f('ix_monitoring_evaluations_support_plan_id'), 'monitoring_evaluations', ['support_plan_id'], unique=False)
    op.create_index(op.f('ix_monitoring_evaluations_created_at'), 'monitoring_evaluations', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_monitoring_evaluations_created_at'), table_name='monitoring_evaluations')
    op.drop_index(op.f('ix_monitoring_evaluations_support_plan_id'), table_name='monitoring_evaluations')
    op.drop_index(op.f('ix_monitoring_evaluations_user_id'), table_name='monitoring_evaluations')
    op.drop_table('monitoring_evaluations')
    op.drop_index(op.f('ix_colorful_pyramids_user_id'), table_name='colorful_pyramids')
    op.drop_table('colorful_pyramids')
    op.drop_index(op.f('ix_assessments_user_id'), table_name='assessments')
    op.drop_table('assessments')
    with op.batch_alter_table('user_daily_reports') as batch:
        batch.drop_column('pulse')
        batch.drop_column('diastolic_bp')
        batch.drop_column('systolic_bp')
        batch.drop_column('body_temperature')
