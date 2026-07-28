from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.wellbeing_cards import CARD_IDS


class WellbeingCardOut(BaseModel):
    id: str
    label: str
    category: str
    description: str


class WellbeingSelectionCreate(BaseModel):
    selection_date: date | None = None  # 未指定なら今日
    card_ids: list[str] = Field(min_length=3, max_length=3)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("card_ids")
    @classmethod
    def validate_card_ids(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("同じカードは1回だけ選べます")
        unknown = [c for c in v if c not in CARD_IDS]
        if unknown:
            raise ValueError(f"存在しないカードが含まれています: {unknown}")
        return v


class WellbeingSelectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    selection_date: date
    card_ids: list[str]
    note: str | None
    created_at: datetime
    updated_at: datetime
