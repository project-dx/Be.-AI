from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StaffRecommendation(BaseModel):
    title: str
    reason: str
    action: str
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    observed_facts: list[str] = []
    hypothesis: str = ""
    questions: list[str] = []
    avoid: str = ""
    next_check_date: str = ""


class UserRecommendation(BaseModel):
    title: str
    reason: str
    action: str
    amount: str = ""       # どのくらい行うか
    alternative: str = ""  # できなかった場合の代替案


class RiskFlag(BaseModel):
    type: str
    detail: str


class AiAnalysisResult(BaseModel):
    """AI分析結果のJSONスキーマ（検証必須）"""

    summary: str
    strengths: list[str] = []
    concerns: list[str] = []
    trend_analysis: str = ""
    maslow_analysis: str = ""
    adler_analysis: str = ""
    perma_analysis: str = ""
    abc_analysis: str = ""
    choice_theory_analysis: str = ""
    behavioral_economics_analysis: str = ""
    staff_recommendations: list[StaffRecommendation] = []
    user_recommendations: list[UserRecommendation] = Field(default=[], max_length=3)
    questions_for_staff: list[str] = []
    risk_flags: list[RiskFlag] = []
    confidence: float = Field(default=0.5, ge=0, le=1)
    data_limitations: list[str] = []


class SupportPlanDraft(BaseModel):
    """AIが生成する個別支援計画の下書きスキーマ"""

    title: str
    current_issues: str
    strengths: str
    user_preferences: str
    background_hypothesis: str
    long_term_goal: str
    short_term_goals: list[str] = []
    support_methods: list[str] = []
    home_actions: list[str] = []
    office_actions: list[str] = []
    user_actions: list[str] = []
    evaluation_metrics: list[str] = []
    notes: str = ""


class AiAnalysisRequest(BaseModel):
    analysis_type: str = Field(default="daily_analysis", pattern="^(daily_analysis|risk_review)$")
    period_days: int = Field(default=14, ge=3, le=90)


class AiAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    analysis_date: date
    analysis_type: str
    input_period_start: date | None
    input_period_end: date | None
    model_name: str
    prompt_version: str
    result_json: dict[str, Any] | None
    status: str
    error_message: str | None
    created_at: datetime
