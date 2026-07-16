from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utcnow


class ScoreResult(Base):
    __tablename__ = "score_results"
    __table_args__ = (UniqueConstraint("user_id", "score_date", name="uq_score_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)

    life_rhythm_score: Mapped[int | None] = mapped_column(Integer)
    sleep_score: Mapped[int | None] = mapped_column(Integer)
    mental_score: Mapped[int | None] = mapped_column(Integer)
    wellbeing_score: Mapped[int | None] = mapped_column(Integer)
    self_efficacy_score: Mapped[int | None] = mapped_column(Integer)
    work_readiness_score: Mapped[int | None] = mapped_column(Integer)
    stress_status: Mapped[str | None] = mapped_column(String(10))  # low/normal/elevated/high

    breakdown_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    calculation_version: Mapped[str] = mapped_column(String(10), default="1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
