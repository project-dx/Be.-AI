from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User, utcnow


class UserDailyReport(Base):
    """利用者日報"""

    __tablename__ = "user_daily_reports"
    __table_args__ = (UniqueConstraint("user_id", "report_date", name="uq_user_report_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)

    mood: Mapped[int | None] = mapped_column(Integer)  # 1..5
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    bedtime: Mapped[str | None] = mapped_column(String(5))  # "HH:MM"
    wake_time: Mapped[str | None] = mapped_column(String(5))
    sleep_quality: Mapped[int | None] = mapped_column(Integer)  # 1..5
    breakfast_status: Mapped[str | None] = mapped_column(String(10))  # eaten / partial / skipped
    lunch_status: Mapped[str | None] = mapped_column(String(10))
    dinner_status: Mapped[str | None] = mapped_column(String(10))
    exercise_minutes: Mapped[int | None] = mapped_column(Integer)
    work_study_minutes: Mapped[int | None] = mapped_column(Integer)
    stress_level: Mapped[int | None] = mapped_column(Integer)  # 1..5
    fatigue_level: Mapped[int | None] = mapped_column(Integer)  # 1..5
    social_level: Mapped[int | None] = mapped_column(Integer)  # 1..5
    achievement: Mapped[str | None] = mapped_column(Text)
    success_experience: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str | None] = mapped_column(Text)
    tomorrow_goal: Mapped[str | None] = mapped_column(Text)
    free_text: Mapped[str | None] = mapped_column(Text)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped[User] = relationship(foreign_keys=[user_id])


class StaffDailyReport(Base):
    """スタッフ日報（支援記録）"""

    __tablename__ = "staff_daily_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    staff_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    report_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    support_minutes: Mapped[int | None] = mapped_column(Integer)
    support_content: Mapped[str | None] = mapped_column(Text)
    user_condition: Mapped[str | None] = mapped_column(Text)
    conversation_summary: Mapped[str | None] = mapped_column(Text)
    positive_points: Mapped[str | None] = mapped_column(Text)
    issues: Mapped[str | None] = mapped_column(Text)
    behavior_changes: Mapped[str | None] = mapped_column(Text)
    support_method: Mapped[str | None] = mapped_column(Text)
    user_response: Mapped[str | None] = mapped_column(Text)
    next_check: Mapped[str | None] = mapped_column(Text)
    urgency: Mapped[str] = mapped_column(String(10), default="normal", nullable=False)  # normal/caution/check/urgent
    free_text: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    staff: Mapped[User] = relationship(foreign_keys=[staff_id])
