from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import utcnow


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False)  # daily_analysis / support_plan / risk_review
    input_period_start: Mapped[date | None] = mapped_column(Date)
    input_period_end: Mapped[date | None] = mapped_column(Date)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(10), default="1.0", nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(10), default="success", nullable=False)  # success/fallback/failed
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True, nullable=False)
