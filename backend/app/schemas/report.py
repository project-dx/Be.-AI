from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

MEAL_PATTERN = "^(eaten|partial|skipped)$"
URGENCY_PATTERN = "^(normal|caution|check|urgent)$"
TIME_PATTERN = r"^([01]?\d|2[0-3]):[0-5]\d$"


class UserDailyReportBase(BaseModel):
    report_date: date
    mood: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    bedtime: str | None = Field(default=None, pattern=TIME_PATTERN)
    wake_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    breakfast_status: str | None = Field(default=None, pattern=MEAL_PATTERN)
    lunch_status: str | None = Field(default=None, pattern=MEAL_PATTERN)
    dinner_status: str | None = Field(default=None, pattern=MEAL_PATTERN)
    exercise_minutes: int | None = Field(default=None, ge=0, le=1440)
    work_study_minutes: int | None = Field(default=None, ge=0, le=1440)
    stress_level: int | None = Field(default=None, ge=1, le=5)
    fatigue_level: int | None = Field(default=None, ge=1, le=5)
    social_level: int | None = Field(default=None, ge=1, le=5)
    achievement: str | None = None
    success_experience: str | None = None
    difficulty: str | None = None
    tomorrow_goal: str | None = None
    free_text: str | None = None
    is_draft: bool = False


# 確定時（is_draft=False）に必須となる項目
REQUIRED_ON_SUBMIT = [
    ("mood", "今日の気分"),
    ("sleep_hours", "睡眠時間"),
    ("sleep_quality", "睡眠の質"),
    ("stress_level", "ストレス"),
    ("fatigue_level", "疲労度"),
    ("social_level", "人との交流"),
]


class UserDailyReportCreate(UserDailyReportBase):
    pass


class UserDailyReportUpdate(BaseModel):
    mood: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    bedtime: str | None = Field(default=None, pattern=TIME_PATTERN)
    wake_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    breakfast_status: str | None = Field(default=None, pattern=MEAL_PATTERN)
    lunch_status: str | None = Field(default=None, pattern=MEAL_PATTERN)
    dinner_status: str | None = Field(default=None, pattern=MEAL_PATTERN)
    exercise_minutes: int | None = Field(default=None, ge=0, le=1440)
    work_study_minutes: int | None = Field(default=None, ge=0, le=1440)
    stress_level: int | None = Field(default=None, ge=1, le=5)
    fatigue_level: int | None = Field(default=None, ge=1, le=5)
    social_level: int | None = Field(default=None, ge=1, le=5)
    achievement: str | None = None
    success_experience: str | None = None
    difficulty: str | None = None
    tomorrow_goal: str | None = None
    free_text: str | None = None
    is_draft: bool | None = None


class UserDailyReportOut(UserDailyReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class StaffDailyReportBase(BaseModel):
    report_date: date
    support_minutes: int | None = Field(default=None, ge=0, le=1440)
    support_content: str | None = None
    user_condition: str | None = None
    conversation_summary: str | None = None
    positive_points: str | None = None
    issues: str | None = None
    behavior_changes: str | None = None
    support_method: str | None = None
    user_response: str | None = None
    next_check: str | None = None
    urgency: str = Field(default="normal", pattern=URGENCY_PATTERN)
    free_text: str | None = None


class StaffDailyReportCreate(StaffDailyReportBase):
    pass


class StaffDailyReportUpdate(BaseModel):
    report_date: date | None = None
    support_minutes: int | None = Field(default=None, ge=0, le=1440)
    support_content: str | None = None
    user_condition: str | None = None
    conversation_summary: str | None = None
    positive_points: str | None = None
    issues: str | None = None
    behavior_changes: str | None = None
    support_method: str | None = None
    user_response: str | None = None
    next_check: str | None = None
    urgency: str | None = Field(default=None, pattern=URGENCY_PATTERN)
    free_text: str | None = None


class StaffDailyReportOut(StaffDailyReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    staff_id: int
    created_at: datetime
    updated_at: datetime
    staff_name: str | None = None
