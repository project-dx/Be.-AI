"""AIへ渡す入力データの構築。

個人を特定できる情報（氏名・メールアドレス・生年月日など）は含めない。
分析に必要な最小限のデータのみを送信する。
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Assessment, ColorfulPyramid, Goal, ScoreResult, StaffDailyReport, UserDailyReport


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def build_analysis_context(db: Session, user_id: int, period_start: date, period_end: date) -> dict[str, Any]:
    reports = (
        db.query(UserDailyReport)
        .filter(
            UserDailyReport.user_id == user_id,
            UserDailyReport.report_date >= period_start,
            UserDailyReport.report_date <= period_end,
            UserDailyReport.is_draft.is_(False),
        )
        .order_by(UserDailyReport.report_date)
        .all()
    )
    staff_reports = (
        db.query(StaffDailyReport)
        .filter(
            StaffDailyReport.user_id == user_id,
            StaffDailyReport.report_date >= period_start,
            StaffDailyReport.report_date <= period_end,
        )
        .order_by(StaffDailyReport.report_date)
        .all()
    )
    scores = (
        db.query(ScoreResult)
        .filter(
            ScoreResult.user_id == user_id,
            ScoreResult.score_date >= period_start,
            ScoreResult.score_date <= period_end,
        )
        .order_by(ScoreResult.score_date)
        .all()
    )
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    assessment = db.query(Assessment).filter(Assessment.user_id == user_id).first()
    pyramid = db.query(ColorfulPyramid).filter(ColorfulPyramid.user_id == user_id).first()

    mid = period_start + (period_end - period_start) / 2
    recent = [r for r in reports if r.report_date > mid]
    earlier = [r for r in reports if r.report_date <= mid]

    def sleep_values(rs: list[UserDailyReport]) -> list[float]:
        return [r.sleep_hours for r in rs if r.sleep_hours is not None]

    def stress_values(rs: list[UserDailyReport]) -> list[float]:
        return [float(r.stress_level) for r in rs if r.stress_level is not None]

    return {
        "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
        "report_count": len(reports),
        "daily_reports": [
            {
                "date": r.report_date.isoformat(),
                "mood": r.mood,
                "sleep_hours": r.sleep_hours,
                "bedtime": r.bedtime,
                "wake_time": r.wake_time,
                "sleep_quality": r.sleep_quality,
                "meals": [r.breakfast_status, r.lunch_status, r.dinner_status],
                "exercise_minutes": r.exercise_minutes,
                "work_study_minutes": r.work_study_minutes,
                "stress_level": r.stress_level,
                "fatigue_level": r.fatigue_level,
                "social_level": r.social_level,
                "vitals": {
                    "body_temperature": r.body_temperature,
                    "systolic_bp": r.systolic_bp,
                    "diastolic_bp": r.diastolic_bp,
                    "pulse": r.pulse,
                },
                "achievement": r.achievement,
                "success_experience": r.success_experience,
                "difficulty": r.difficulty,
                "tomorrow_goal": r.tomorrow_goal,
                "free_text": r.free_text,
            }
            for r in reports
        ],
        "staff_reports": [
            {
                "date": s.report_date.isoformat(),
                "urgency": s.urgency,
                "support_content": s.support_content,
                "user_condition": s.user_condition,
                "positive_points": s.positive_points,
                "issues": s.issues,
                "behavior_changes": s.behavior_changes,
            }
            for s in staff_reports
        ],
        "scores": [
            {
                "date": s.score_date.isoformat(),
                "life_rhythm": s.life_rhythm_score,
                "sleep": s.sleep_score,
                "mental": s.mental_score,
                "wellbeing": s.wellbeing_score,
                "self_efficacy": s.self_efficacy_score,
                "work_readiness": s.work_readiness_score,
                "stress_status": s.stress_status,
            }
            for s in scores
        ],
        "goals": [{"title": g.title, "progress": g.progress} for g in goals],
        # 初期アセスメント（個別支援計画のパーソナライズに用いる）
        "assessment": {
            "life_history": assessment.life_history,
            "disability_characteristics": assessment.disability_characteristics,
            "thinking_style": assessment.thinking_style,
            "herrmann_model": {
                "a_logical": assessment.herrmann_a,
                "b_practical": assessment.herrmann_b,
                "c_relational": assessment.herrmann_c,
                "d_creative": assessment.herrmann_d,
            },
            "personal_values": assessment.personal_values,
            "strengths": assessment.strengths,
            "support_needs": assessment.support_needs,
        }
        if assessment
        else None,
        # カラフルピラミッド（本人の価値観・目指す姿）
        "pyramid": {
            "wellbeing": pyramid.wellbeing,
            "passion": pyramid.passion,
            "vision": pyramid.vision,
            "mission": pyramid.mission,
        }
        if pyramid
        else None,
        "stats": {
            "avg_sleep_recent": _avg(sleep_values(recent)),
            "avg_sleep_earlier": _avg(sleep_values(earlier)),
            "avg_stress_recent": _avg(stress_values(recent)),
            "avg_stress_earlier": _avg(stress_values(earlier)),
            "success_experience_days": sum(1 for r in reports if (r.success_experience or "").strip()),
            "avg_mood": _avg([float(r.mood) for r in reports if r.mood is not None]),
        },
    }


def default_period(period_days: int, today: date | None = None) -> tuple[date, date]:
    end = today or date.today()
    return end - timedelta(days=period_days - 1), end
