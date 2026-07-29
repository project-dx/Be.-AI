from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class MonthlyUserAnalysis(BaseModel):
    """月次レポートの利用者別分析（AIには氏名を渡さずuser_idで紐付ける）"""

    user_id: int
    mental: str  # メンタル面の傾向
    condition: str  # 体調面の傾向
    skill: str  # スキル・活動の傾向
    plan: str  # 傾向と対策

    display_name: str = ""  # サーバー側で付与（AI出力には含まれない）


class ActionPlanStep(BaseModel):
    title: str
    detail: str


class MonthlyReportResult(BaseModel):
    """月次レポートのAI生成部分のスキーマ（検証必須）"""

    analysis_points: str  # 全体の分析ポイント
    skill_trends: str  # 事業所全体のスキル傾向
    user_analyses: list[MonthlyUserAnalysis] = []
    action_plan: list[ActionPlanStep] = Field(default=[], max_length=5)
    data_limitations: list[str] = []
    confidence: float = Field(default=0.5, ge=0, le=1)


class MonthlyReportRequest(BaseModel):
    year_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # 例: 2026-07


class MonthlyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    year_month: str
    period_start: date
    period_end: date
    model_name: str
    prompt_version: str
    facts_json: dict[str, Any] | None
    result_json: dict[str, Any] | None
    status: str
    error_message: str | None
    created_at: datetime


class AiAnalysisRequest(BaseModel):
    analysis_type: str = Field(default="daily_analysis", pattern="^(daily_analysis|risk_review)$")
    period_days: int = Field(default=14, ge=3, le=90)
    # カレンダーで期間を選ぶ場合はこちらを使う（両方指定されたときはこちらを優先）
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def validate_period(self) -> "AiAnalysisRequest":
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("期間は開始日と終了日の両方を指定してください")
        if self.period_start and self.period_end:
            if self.period_start > self.period_end:
                raise ValueError("開始日は終了日より前の日付にしてください")
            if (self.period_end - self.period_start).days > 365:
                raise ValueError("期間は1年以内で指定してください")
        return self


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
