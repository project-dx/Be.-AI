from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScoreResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    score_date: date
    life_rhythm_score: int | None
    sleep_score: int | None
    mental_score: int | None
    wellbeing_score: int | None
    self_efficacy_score: int | None
    work_readiness_score: int | None
    stress_status: str | None
    breakdown_json: dict[str, Any] | None
    calculation_version: str


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    target_date: date | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    target_date: date | None = None
    status: str | None = Field(default=None, pattern="^(active|achieved|paused|closed)$")
    progress: int | None = Field(default=None, ge=0, le=100)


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    description: str | None
    target_date: date | None
    status: str
    progress: int
    created_at: datetime
    updated_at: datetime


class RiskAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    alert_type: str
    severity: str
    reason: str
    source_data_json: dict[str, Any] | None
    status: str
    acknowledged_by: int | None
    acknowledged_at: datetime | None
    created_at: datetime
    user_name: str | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_user_id: int | None
    action: str
    target_type: str | None
    target_id: int | None
    details_json: dict[str, Any] | None
    created_at: datetime
    actor_email: str | None = None


class ScoringWeightsUpdate(BaseModel):
    weights: dict[str, Any]
