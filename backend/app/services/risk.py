"""ルールベースのリスク検知。

医療診断や自動的な断定は行わない。検知結果は「スタッフによる確認が必要」な
参考情報としてダッシュボードに表示され、外部への自動通報は行わない。
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import RiskAlert, ScoreResult, StaffDailyReport, UserDailyReport

# 危険性を示す可能性のある表現（誤検知前提。必ずスタッフ確認を促す）
RISKY_KEYWORDS = [
    "死にたい",
    "消えたい",
    "いなくなりたい",
    "自傷",
    "リストカット",
    "自殺",
    "死のう",
    "殴られ",
    "叩かれ",
    "暴力",
    "虐待",
    "オーバードーズ",
]

CONFIRM_NOTE = "スタッフによる確認が必要です（自動判定のため誤検知の可能性があります）"


def _create_alert_if_new(
    db: Session,
    user_id: int,
    alert_type: str,
    severity: str,
    reason: str,
    source: dict[str, Any] | None = None,
) -> RiskAlert | None:
    """同一利用者・同一タイプの未確認アラートが無い場合のみ作成。"""
    existing = (
        db.query(RiskAlert)
        .filter(
            RiskAlert.user_id == user_id,
            RiskAlert.alert_type == alert_type,
            RiskAlert.status == "open",
        )
        .first()
    )
    if existing is not None:
        return None
    alert = RiskAlert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        reason=reason,
        source_data_json=source,
    )
    db.add(alert)
    return alert


def evaluate_user_risks(db: Session, user_id: int, as_of: date) -> list[RiskAlert]:
    """利用者日報に基づくリスク判定。作成されたアラートを返す。"""
    created: list[RiskAlert] = []
    week_start = as_of - timedelta(days=6)
    reports = (
        db.query(UserDailyReport)
        .filter(
            UserDailyReport.user_id == user_id,
            UserDailyReport.report_date >= week_start,
            UserDailyReport.report_date <= as_of,
            UserDailyReport.is_draft.is_(False),
        )
        .order_by(UserDailyReport.report_date)
        .all()
    )
    by_date = {r.report_date: r for r in reports}
    last3_dates = [as_of - timedelta(days=i) for i in range(3)]

    # ストレス5が3日連続
    if all(d in by_date and by_date[d].stress_level == 5 for d in last3_dates):
        alert = _create_alert_if_new(
            db, user_id, "stress_high_streak", "high",
            f"ストレス自己評価5が3日連続しています。{CONFIRM_NOTE}",
            {"dates": [d.isoformat() for d in last3_dates]},
        )
        if alert:
            created.append(alert)

    # 気分1が3日連続
    if all(d in by_date and by_date[d].mood == 1 for d in last3_dates):
        alert = _create_alert_if_new(
            db, user_id, "mood_low_streak", "high",
            f"気分の自己評価1が3日連続しています。{CONFIRM_NOTE}",
            {"dates": [d.isoformat() for d in last3_dates]},
        )
        if alert:
            created.append(alert)

    # 睡眠時間3時間未満
    today_report = by_date.get(as_of)
    if today_report and today_report.sleep_hours is not None and today_report.sleep_hours < 3:
        alert = _create_alert_if_new(
            db, user_id, "sleep_critical", "high",
            f"睡眠時間が{today_report.sleep_hours}時間と極端に短くなっています。{CONFIRM_NOTE}",
            {"date": as_of.isoformat(), "sleep_hours": today_report.sleep_hours},
        )
        if alert:
            created.append(alert)

    # 危険性を示す表現
    if today_report:
        text = " ".join(filter(None, [today_report.difficulty, today_report.free_text]))
        hits = [kw for kw in RISKY_KEYWORDS if kw in text]
        if hits:
            alert = _create_alert_if_new(
                db, user_id, "risky_expression", "high",
                f"日報に注意が必要な可能性のある表現が含まれています。{CONFIRM_NOTE}",
                {"date": as_of.isoformat(), "matched_count": len(hits)},
            )
            if alert:
                created.append(alert)

    # 日報の急な途切れ（直近3日なし、その前4日で1件以上）
    recent3 = [as_of - timedelta(days=i) for i in range(3)]
    earlier4 = [as_of - timedelta(days=i) for i in range(3, 7)]
    if not any(d in by_date for d in recent3) and any(d in by_date for d in earlier4):
        alert = _create_alert_if_new(
            db, user_id, "report_gap", "medium",
            f"日報の入力が3日以上途切れています。{CONFIRM_NOTE}",
            {"as_of": as_of.isoformat()},
        )
        if alert:
            created.append(alert)

    # メンタルスコアの急低下（7日平均比25点以上）
    scores = (
        db.query(ScoreResult)
        .filter(
            ScoreResult.user_id == user_id,
            ScoreResult.score_date >= as_of - timedelta(days=7),
            ScoreResult.score_date < as_of,
            ScoreResult.mental_score.isnot(None),
        )
        .all()
    )
    today_score = (
        db.query(ScoreResult)
        .filter(ScoreResult.user_id == user_id, ScoreResult.score_date == as_of)
        .first()
    )
    if scores and today_score and today_score.mental_score is not None:
        avg = sum(s.mental_score for s in scores) / len(scores)
        if avg - today_score.mental_score >= 25:
            alert = _create_alert_if_new(
                db, user_id, "score_drop", "medium",
                f"メンタルスコアが直近平均より{round(avg - today_score.mental_score)}点低下しています。{CONFIRM_NOTE}",
                {"avg_7d": round(avg, 1), "today": today_score.mental_score},
            )
            if alert:
                created.append(alert)

    return created


def evaluate_staff_report_risk(db: Session, report: StaffDailyReport) -> RiskAlert | None:
    """スタッフ日報の緊急度「至急」でアラートを作成。"""
    if report.urgency != "urgent":
        return None
    return _create_alert_if_new(
        db, report.user_id, "staff_urgent", "high",
        f"スタッフ日報で緊急度「至急」が記録されました。{CONFIRM_NOTE}",
        {"staff_report_id": report.id, "report_date": report.report_date.isoformat()},
    )
