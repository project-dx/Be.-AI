from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SupportPlanBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    current_issues: str | None = None
    strengths: str | None = None
    user_preferences: str | None = None
    background_hypothesis: str | None = None
    long_term_goal: str | None = None
    short_term_goals_json: list[str] | None = None
    support_methods_json: list[str] | None = None
    home_actions_json: list[str] | None = None
    office_actions_json: list[str] | None = None
    user_actions_json: list[str] | None = None
    evaluation_metrics_json: list[str] | None = None
    evaluation_date: date | None = None
    next_review_date: date | None = None
    notes: str | None = None


class SupportPlanCreate(SupportPlanBase):
    pass


class SupportPlanUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern="^(draft|in_review|approved|active|evaluated|closed)$")
    current_issues: str | None = None
    strengths: str | None = None
    user_preferences: str | None = None
    background_hypothesis: str | None = None
    long_term_goal: str | None = None
    short_term_goals_json: list[str] | None = None
    support_methods_json: list[str] | None = None
    home_actions_json: list[str] | None = None
    office_actions_json: list[str] | None = None
    user_actions_json: list[str] | None = None
    evaluation_metrics_json: list[str] | None = None
    evaluation_date: date | None = None
    next_review_date: date | None = None
    notes: str | None = None
    change_reason: str | None = None


class SupportPlanOut(SupportPlanBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    status: str
    created_by: int | None
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SupportPlanVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    support_plan_id: int
    version_number: int
    snapshot_json: dict[str, Any]
    changed_by: int | None
    change_reason: str | None
    created_at: datetime


class SupportActionCreate(BaseModel):
    support_plan_id: int | None = None
    action_date: date
    action_content: str = Field(min_length=1)
    user_response: str | None = None
    effect_score: int | None = Field(default=None, ge=1, le=5)
    next_action: str | None = None


class SupportActionOut(SupportActionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    staff_id: int
    created_at: datetime
