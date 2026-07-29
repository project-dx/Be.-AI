from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- 初期アセスメント ---
class AssessmentBase(BaseModel):
    assessment_date: date | None = None
    life_history: str | None = None
    disability_characteristics: str | None = None
    thinking_style: str | None = None
    herrmann_a: int | None = Field(default=None, ge=0, le=100)
    herrmann_b: int | None = Field(default=None, ge=0, le=100)
    herrmann_c: int | None = Field(default=None, ge=0, le=100)
    herrmann_d: int | None = Field(default=None, ge=0, le=100)
    personal_values: str | None = None
    strengths: str | None = None
    support_needs: str | None = None
    notes: str | None = None


class AssessmentUpsert(AssessmentBase):
    pass


class AssessmentOut(AssessmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    assessment_date: date
    created_at: datetime
    updated_at: datetime


# --- カラフルピラミッド ---
class PyramidUpsert(BaseModel):
    wellbeing: str | None = None
    passion: str | None = None
    vision: str | None = None
    mission: str | None = None


class PyramidOut(PyramidUpsert):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# --- モニタリング評価 ---
class MonitoringGenerateRequest(BaseModel):
    period_months: int = Field(default=6, ge=1, le=12)


class MonitoringUpdate(BaseModel):
    achievements: str | None = None
    challenges: str | None = None
    plan_adjustments: str | None = None
    next_period_focus: str | None = None
    staff_comment: str | None = None


class MonitoringOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    support_plan_id: int | None
    evaluation_date: date
    period_start: date
    period_end: date
    score_summary_json: dict[str, Any] | None
    achievements: str | None
    challenges: str | None
    plan_adjustments: str | None
    next_period_focus: str | None
    staff_comment: str | None
    ai_generated: bool
    model_name: str | None
    created_at: datetime
    updated_at: datetime
