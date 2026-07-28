from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User, utcnow


class WellbeingCardSelection(Base):
    """利用者が選んだウェルビーイングカード（1日1件・3枚選択）"""

    __tablename__ = "wellbeing_card_selections"
    __table_args__ = (UniqueConstraint("user_id", "selection_date", name="uq_wellbeing_selection_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    selection_date: Mapped[date] = mapped_column(Date, nullable=False)
    card_ids: Mapped[list[Any]] = mapped_column(JSON, nullable=False)  # 選んだ順の3枚のカードID
    note: Mapped[str | None] = mapped_column(Text)  # 選んだ理由・気持ち（任意）

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
