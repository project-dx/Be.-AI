"""ルールベースのスコア計算エンジン。

docs/scoring-rules.md（calculation_version 1.0）に準拠する。
各コンポーネントは「比率(0..1) × 配点」で計算し、配点は
system_settings の scoring_weights で将来変更できる。
"""

from datetime import date, timedelta
from statistics import pstdev
from typing import Any

from sqlalchemy.orm import Session

from app.models import Goal, ScoreResult, SystemSetting, UserDailyReport

CALCULATION_VERSION = "1.0"

DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "sleep": {"duration": 40, "quality": 25, "bedtime_stability": 15, "wake_stability": 20},
    "life_rhythm": {"wake_stability": 25, "bedtime_stability": 20, "meals": 20, "exercise": 15, "activity": 20},
    "mental": {"mood": 30, "stress": 30, "fatigue": 20, "social": 20},
    "wellbeing": {"positive_emotion": 20, "engagement": 20, "relationships": 20, "meaning": 20, "accomplishment": 20},
    "self_efficacy": {"success": 30, "goals": 25, "self_eval": 25, "continuity": 20},
    "work_readiness": {"wake_stability": 25, "report_rate": 20, "work_time": 25, "plan_execution": 15, "stress_mgmt": 15},
}

# 安定性（標準偏差・分）の比率。データ2日未満は中立値 0.65
STABILITY_NEUTRAL = 0.65


def get_weights(db: Session) -> dict[str, dict[str, float]]:
    """設定テーブルから配点を取得（無ければ初期値）。"""
    row = db.query(SystemSetting).filter(SystemSetting.setting_key == "scoring_weights").first()
    weights = {k: dict(v) for k, v in DEFAULT_WEIGHTS.items()}
    if row and isinstance(row.setting_value_json, dict):
        for group, values in row.setting_value_json.items():
            if group in weights and isinstance(values, dict):
                for key, val in values.items():
                    if key in weights[group] and isinstance(val, (int, float)):
                        weights[group][key] = float(val)
    return weights


# --- 比率計算ヘルパー ---


def scale5_ratio(value: int | None, positive: bool = True) -> float | None:
    """1..5 の値を 0..1 に変換。positive=False は逆向き（5が悪い）。None は None。"""
    if value is None:
        return None
    v = max(1, min(5, value))
    return (v - 1) / 4 if positive else (5 - v) / 4


def sleep_duration_ratio(hours: float | None) -> float | None:
    if hours is None:
        return None
    if 7 <= hours <= 9:
        return 1.0
    if 6 <= hours < 7 or 9 < hours <= 10:
        return 0.75
    if 5 <= hours < 6 or 10 < hours <= 11:
        return 0.5
    if 4 <= hours < 5:
        return 0.25
    return 0.0


def time_to_minutes(hhmm: str | None, anchor_minutes: int = 0) -> int | None:
    """"HH:MM" を anchor からの経過分に正規化（就寝は18:00起点で深夜跨ぎ対応）。"""
    if not hhmm or ":" not in hhmm:
        return None
    try:
        h, m = hhmm.split(":")
        total = int(h) * 60 + int(m)
    except ValueError:
        return None
    return (total - anchor_minutes) % 1440


def stability_ratio(minutes_list: list[int]) -> tuple[float, bool]:
    """時刻リストの安定性比率と、データ不足フラグを返す。"""
    if len(minutes_list) < 2:
        return STABILITY_NEUTRAL, True
    sigma = pstdev(minutes_list)
    if sigma <= 30:
        return 1.0, False
    if sigma <= 60:
        return 0.7, False
    if sigma <= 90:
        return 0.35, False
    return 0.0, False


def meal_ratio(*statuses: str | None) -> float:
    points = {"eaten": 1.0, "partial": 0.5, "skipped": 0.0}
    return sum(points.get(s or "", 0.0) for s in statuses) / len(statuses)


def step_ratio(value: float | None, steps: list[tuple[float, float]]) -> float | None:
    """steps: [(しきい値, 比率), ...] 降順。value >= しきい値 で最初に一致した比率。"""
    if value is None:
        return None
    for threshold, ratio in steps:
        if value >= threshold:
            return ratio
    return 0.0


EXERCISE_STEPS = [(30, 1.0), (15, 0.667), (5, 0.333)]
ACTIVITY_STEPS = [(240, 1.0), (120, 0.75), (60, 0.5), (30, 0.25)]
ENGAGEMENT_STEPS = [(180, 1.0), (120, 0.75), (60, 0.5), (15, 0.25)]
WORK_AVG_STEPS = [(240, 1.0), (120, 0.72), (60, 0.4), (30, 0.2)]


def _component(breakdown: dict, missing: list[str], name: str, ratio: float | None, weight: float) -> float:
    """比率×配点を点数化して breakdown へ記録。欠損は0点+missing記録。"""
    if ratio is None:
        missing.append(name)
        breakdown[name] = {"points": 0, "max": weight, "missing": True}
        return 0.0
    points = ratio * weight
    breakdown[name] = {"points": round(points, 1), "max": weight}
    return points


def _finalize(total: float) -> int:
    return max(0, min(100, round(total)))


# --- 各スコア ---


def calc_sleep_score(today: UserDailyReport, week: list[UserDailyReport], w: dict[str, float]) -> tuple[int, dict]:
    breakdown: dict[str, Any] = {}
    missing: list[str] = []
    total = _component(breakdown, missing, "duration", sleep_duration_ratio(today.sleep_hours), w["duration"])
    total += _component(breakdown, missing, "quality", scale5_ratio(today.sleep_quality), w["quality"])

    bed_minutes = [m for r in week if (m := time_to_minutes(r.bedtime, anchor_minutes=18 * 60)) is not None]
    wake_minutes = [m for r in week if (m := time_to_minutes(r.wake_time)) is not None]
    bed_ratio, bed_short = stability_ratio(bed_minutes)
    wake_ratio, wake_short = stability_ratio(wake_minutes)
    total += _component(breakdown, missing, "bedtime_stability", bed_ratio, w["bedtime_stability"])
    total += _component(breakdown, missing, "wake_stability", wake_ratio, w["wake_stability"])
    if bed_short or wake_short:
        breakdown["insufficient_data"] = True
    if missing:
        breakdown["missing_fields"] = missing
    return _finalize(total), breakdown


def calc_life_rhythm_score(today: UserDailyReport, week: list[UserDailyReport], w: dict[str, float]) -> tuple[int, dict]:
    breakdown: dict[str, Any] = {}
    missing: list[str] = []
    bed_minutes = [m for r in week if (m := time_to_minutes(r.bedtime, anchor_minutes=18 * 60)) is not None]
    wake_minutes = [m for r in week if (m := time_to_minutes(r.wake_time)) is not None]
    wake_ratio, wake_short = stability_ratio(wake_minutes)
    bed_ratio, bed_short = stability_ratio(bed_minutes)
    total = _component(breakdown, missing, "wake_stability", wake_ratio, w["wake_stability"])
    total += _component(breakdown, missing, "bedtime_stability", bed_ratio, w["bedtime_stability"])
    total += _component(
        breakdown, missing, "meals",
        meal_ratio(today.breakfast_status, today.lunch_status, today.dinner_status), w["meals"],
    )
    total += _component(breakdown, missing, "exercise", step_ratio(today.exercise_minutes, EXERCISE_STEPS), w["exercise"])
    total += _component(breakdown, missing, "activity", step_ratio(today.work_study_minutes, ACTIVITY_STEPS), w["activity"])
    if wake_short or bed_short:
        breakdown["insufficient_data"] = True
    if missing:
        breakdown["missing_fields"] = missing
    return _finalize(total), breakdown


def calc_mental_score(today: UserDailyReport, w: dict[str, float]) -> tuple[int, dict]:
    breakdown: dict[str, Any] = {}
    missing: list[str] = []
    total = _component(breakdown, missing, "mood", scale5_ratio(today.mood), w["mood"])
    total += _component(breakdown, missing, "stress", scale5_ratio(today.stress_level, positive=False), w["stress"])
    total += _component(breakdown, missing, "fatigue", scale5_ratio(today.fatigue_level, positive=False), w["fatigue"])
    total += _component(breakdown, missing, "social", scale5_ratio(today.social_level), w["social"])
    if missing:
        breakdown["missing_fields"] = missing
    return _finalize(total), breakdown


def calc_wellbeing_score(today: UserDailyReport, w: dict[str, float]) -> tuple[int, dict]:
    breakdown: dict[str, Any] = {}
    missing: list[str] = []
    total = _component(breakdown, missing, "positive_emotion", scale5_ratio(today.mood), w["positive_emotion"])
    engagement_minutes = (today.work_study_minutes or 0) + (today.exercise_minutes or 0)
    total += _component(breakdown, missing, "engagement", step_ratio(engagement_minutes, ENGAGEMENT_STEPS), w["engagement"])
    total += _component(breakdown, missing, "relationships", scale5_ratio(today.social_level), w["relationships"])
    meaning_ratio = 1.0 if (today.tomorrow_goal or "").strip() else 0.0
    total += _component(breakdown, missing, "meaning", meaning_ratio, w["meaning"])
    accomplishment_ratio = (0.6 if (today.success_experience or "").strip() else 0.0) + (
        0.4 if (today.achievement or "").strip() else 0.0
    )
    total += _component(breakdown, missing, "accomplishment", accomplishment_ratio, w["accomplishment"])
    if missing:
        breakdown["missing_fields"] = missing
    return _finalize(total), breakdown


def calc_self_efficacy_score(
    week: list[UserDailyReport], goals: list[Goal], w: dict[str, float]
) -> tuple[int, dict]:
    breakdown: dict[str, Any] = {}
    missing: list[str] = []
    success_days = sum(1 for r in week if (r.success_experience or "").strip())
    total = _component(breakdown, missing, "success", success_days / 7, w["success"])

    active_goals = [g for g in goals if g.status == "active"]
    if active_goals:
        goal_ratio = sum(g.progress for g in active_goals) / len(active_goals) / 100
    else:
        goal_ratio = 0.48  # 目標未登録時の中立値（12/25点相当）
        breakdown["no_goals"] = True
    total += _component(breakdown, missing, "goals", goal_ratio, w["goals"])

    moods = [r.mood for r in week if r.mood is not None]
    mood_ratio = ((sum(moods) / len(moods)) - 1) / 4 if moods else None
    total += _component(breakdown, missing, "self_eval", mood_ratio, w["self_eval"])
    total += _component(breakdown, missing, "continuity", len(week) / 7, w["continuity"])
    if missing:
        breakdown["missing_fields"] = missing
    return _finalize(total), breakdown


def calc_work_readiness_score(week: list[UserDailyReport], w: dict[str, float]) -> tuple[int, dict]:
    breakdown: dict[str, Any] = {}
    missing: list[str] = []
    wake_minutes = [m for r in week if (m := time_to_minutes(r.wake_time)) is not None]
    wake_ratio, wake_short = stability_ratio(wake_minutes)
    total = _component(breakdown, missing, "wake_stability", wake_ratio, w["wake_stability"])
    total += _component(breakdown, missing, "report_rate", len(week) / 7, w["report_rate"])

    work_values = [r.work_study_minutes for r in week if r.work_study_minutes is not None]
    work_avg = sum(work_values) / len(work_values) if work_values else None
    total += _component(breakdown, missing, "work_time", step_ratio(work_avg, WORK_AVG_STEPS), w["work_time"])

    plan_days = sum(1 for r in week if (r.tomorrow_goal or "").strip())
    total += _component(breakdown, missing, "plan_execution", plan_days / 7, w["plan_execution"])

    stress_values = [r.stress_level for r in week if r.stress_level is not None]
    if stress_values:
        avg = sum(stress_values) / len(stress_values)
        stress_ratio = 1.0 if avg <= 2 else 0.667 if avg <= 3 else 0.333 if avg <= 4 else 0.0
    else:
        stress_ratio = None
    total += _component(breakdown, missing, "stress_mgmt", stress_ratio, w["stress_mgmt"])
    if wake_short:
        breakdown["insufficient_data"] = True
    if missing:
        breakdown["missing_fields"] = missing
    return _finalize(total), breakdown


def calc_stress_status(reports_last3: list[UserDailyReport]) -> str | None:
    """直近3日間（データがある日）のストレス平均から4段階判定。"""
    values = [r.stress_level for r in reports_last3 if r.stress_level is not None]
    if not values:
        return None
    avg = sum(values) / len(values)
    if avg <= 2.0:
        return "low"
    if avg <= 3.0:
        return "normal"
    if avg <= 4.0:
        return "elevated"
    return "high"


# --- エントリポイント ---


def calculate_scores_for_date(
    db: Session, user_id: int, target_date: date, weights: dict[str, dict[str, float]] | None = None
) -> ScoreResult | None:
    """対象日のスコアを計算して score_results に保存（upsert）する。

    対象日の確定日報が無い場合は None を返す。
    """
    if weights is None:
        weights = get_weights(db)

    week_start = target_date - timedelta(days=6)
    week = (
        db.query(UserDailyReport)
        .filter(
            UserDailyReport.user_id == user_id,
            UserDailyReport.report_date >= week_start,
            UserDailyReport.report_date <= target_date,
            UserDailyReport.is_draft.is_(False),
        )
        .order_by(UserDailyReport.report_date)
        .all()
    )
    today = next((r for r in week if r.report_date == target_date), None)
    if today is None:
        return None

    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    last3 = [r for r in week if r.report_date >= target_date - timedelta(days=2)]

    sleep_score, sleep_bd = calc_sleep_score(today, week, weights["sleep"])
    life_score, life_bd = calc_life_rhythm_score(today, week, weights["life_rhythm"])
    mental_score, mental_bd = calc_mental_score(today, weights["mental"])
    wellbeing_score, wellbeing_bd = calc_wellbeing_score(today, weights["wellbeing"])
    efficacy_score, efficacy_bd = calc_self_efficacy_score(week, goals, weights["self_efficacy"])
    work_score, work_bd = calc_work_readiness_score(week, weights["work_readiness"])
    stress_status = calc_stress_status(last3)

    breakdown = {
        "sleep": sleep_bd,
        "life_rhythm": life_bd,
        "mental": mental_bd,
        "wellbeing": wellbeing_bd,
        "self_efficacy": efficacy_bd,
        "work_readiness": work_bd,
        "report_days_in_week": len(week),
    }

    result = (
        db.query(ScoreResult)
        .filter(ScoreResult.user_id == user_id, ScoreResult.score_date == target_date)
        .first()
    )
    if result is None:
        result = ScoreResult(user_id=user_id, score_date=target_date)
        db.add(result)
    result.sleep_score = sleep_score
    result.life_rhythm_score = life_score
    result.mental_score = mental_score
    result.wellbeing_score = wellbeing_score
    result.self_efficacy_score = efficacy_score
    result.work_readiness_score = work_score
    result.stress_status = stress_status
    result.breakdown_json = breakdown
    result.calculation_version = CALCULATION_VERSION
    return result


def recalculate_range(db: Session, user_id: int, date_from: date, date_to: date) -> int:
    """期間内の全日を再計算し、計算できた日数を返す。"""
    weights = get_weights(db)
    count = 0
    current = date_from
    while current <= date_to:
        if calculate_scores_for_date(db, user_id, current, weights) is not None:
            count += 1
        current += timedelta(days=1)
    return count
