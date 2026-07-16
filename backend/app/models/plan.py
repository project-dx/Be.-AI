from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utcnow

# 支援計画の状態: draft / in_review / approved / active / evaluated / closed
PLAN_STATUSES = ["draft", "in_review", "approved", "active", "evaluated", "closed"]


class SupportPlan(Base):
    __tablename__ = "support_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    current_issues: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[str | None] = mapped_column(Text)
    user_preferences: Mapped[str | None] = mapped_column(Text)  # 本人の希望
    background_hypothesis: Mapped[str | None] = mapped_column(Text)
    long_term_goal: Mapped[str | None] = mapped_column(Text)
    short_term_goals_json: Mapped[list[Any] | None] = mapped_column(JSON)
    support_methods_json: Mapped[list[Any] | None] = mapped_column(JSON)
    home_actions_json: Mapped[list[Any] | None] = mapped_column(JSON)
    office_actions_json: Mapped[list[Any] | None] = mapped_column(JSON)
    user_actions_json: Mapped[list[Any] | None] = mapped_column(JSON)
    evaluation_metrics_json: Mapped[list[Any] | None] = mapped_column(JSON)
    evaluation_date: Mapped[date | None] = mapped_column(Date)
    next_review_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)  # 注意事項

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class SupportPlanVersion(Base):
    __tablename__ = "support_plan_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    support_plan_id: Mapped[int] = mapped_column(ForeignKey("support_plans.id"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    change_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class SupportAction(Base):
    """支援実施記録（効果測定）"""

    __tablename__ = "support_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    support_plan_id: Mapped[int | None] = mapped_column(ForeignKey("support_plans.id"), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    action_content: Mapped[str] = mapped_column(Text, nullable=False)
    user_response: Mapped[str | None] = mapped_column(Text)
    effect_score: Mapped[int | None] = mapped_column(Integer)  # 1..5
    next_action: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
