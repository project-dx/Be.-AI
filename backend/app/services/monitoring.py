"""6か月ごとのモニタリング評価の下書き生成。

スコアの推移・目標の達成状況・支援記録から、評価の下書きを組み立てる。
断定を避け、スタッフが編集・確定することを前提とした文面にする。
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Goal, ScoreResult, StaffDailyReport, SupportPlan, UserDailyReport

SCORE_FIELDS = [
    ("life_rhythm_score", "生活リズム"),
    ("sleep_score", "睡眠"),
    ("mental_score", "メンタル"),
    ("wellbeing_score", "幸福度(PERMA)"),
    ("self_efficacy_score", "自己効力感"),
    ("work_readiness_score", "就労準備度"),
]


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def build_monitoring_draft(db: Session, user_id: int, period_months: int = 6) -> dict[str, Any] | None:
    period_end = date.today()
    period_start = period_end - timedelta(days=period_months * 30)

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
    if not reports:
        return None

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
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    plan = (
        db.query(SupportPlan)
        .filter(SupportPlan.user_id == user_id)
        .order_by(SupportPlan.created_at.desc())
        .first()
    )
    staff_reports = (
        db.query(StaffDailyReport)
        .filter(
            StaffDailyReport.user_id == user_id,
            StaffDailyReport.report_date >= period_start,
            StaffDailyReport.report_date <= period_end,
        )
        .all()
    )

    # --- スコアの前半／後半比較 ---
    mid = period_start + (period_end - period_start) / 2
    first_half = [s for s in scores if s.score_date <= mid]
    second_half = [s for s in scores if s.score_date > mid]

    score_summary: dict[str, Any] = {
        "period_months": period_months,
        "report_count": len(reports),
        "score_count": len(scores),
        "scores": {},
    }
    improved: list[str] = []
    declined: list[str] = []

    for field, label in SCORE_FIELDS:
        before = _avg([getattr(s, field) for s in first_half if getattr(s, field) is not None])
        after = _avg([getattr(s, field) for s in second_half if getattr(s, field) is not None])
        score_summary["scores"][field] = {"label": label, "before": before, "after": after}
        if before is not None and after is not None:
            diff = round(after - before, 1)
            score_summary["scores"][field]["diff"] = diff
            if diff >= 5:
                improved.append(f"{label}（{before}→{after}点）")
            elif diff <= -5:
                declined.append(f"{label}（{before}→{after}点）")

    # --- 達成できたこと ---
    achieved_goals = [g for g in goals if g.status == "achieved" or (g.progress or 0) >= 80]
    success_days = sum(1 for r in reports if (r.success_experience or "").strip())
    achievements_parts = [
        f"期間中に{len(reports)}日分の日報を記録し、生活状況を継続的に把握できました。"
    ]
    if improved:
        achievements_parts.append("スコアでは" + "、".join(improved) + "の改善傾向が見られます。")
    if achieved_goals:
        achievements_parts.append(
            "目標では「" + "」「".join(g.title for g in achieved_goals[:3]) + "」に到達しています。"
        )
    if success_days:
        achievements_parts.append(f"成功体験の記録が{success_days}日分あり、自己効力感につながる行動が続いています。")

    # --- 残された課題 ---
    challenges_parts: list[str] = []
    if declined:
        challenges_parts.append("スコアでは" + "、".join(declined) + "に低下傾向が見られ、要因の確認が必要です。")
    ongoing_goals = [g for g in goals if g.status == "active" and (g.progress or 0) < 80]
    if ongoing_goals:
        challenges_parts.append(
            "「" + "」「".join(g.title for g in ongoing_goals[:3]) + "」は継続中で、達成に向けた支援の調整が必要です。"
        )
    urgent_count = sum(1 for s in staff_reports if s.urgency in ("check", "urgent"))
    if urgent_count:
        challenges_parts.append(f"期間中に確認・至急の対応を要する支援記録が{urgent_count}件ありました。")
    if not challenges_parts:
        challenges_parts.append("大きな課題は確認されていませんが、現在の生活リズムの維持が引き続き必要です。")

    # --- 支援計画の調整 ---
    adjustments_parts: list[str] = []
    if plan:
        adjustments_parts.append(f"現在の支援計画「{plan.title}」の内容を本人と一緒に振り返ります。")
    if declined:
        adjustments_parts.append("低下傾向が見られる項目については、目標を一段小さくし、達成しやすい形へ見直します。")
    if improved:
        adjustments_parts.append("改善が見られる項目は現在の支援を継続し、本人へ具体的に成果を伝えます。")
    if not adjustments_parts:
        adjustments_parts.append("現在の支援内容を継続し、本人の希望に応じて活動の幅を広げることを検討します。")

    # --- 次期の重点 ---
    focus_parts = ["本人の希望を確認したうえで、次期の目標を1〜2つに絞って設定します。"]
    if declined:
        focus_parts.append("低下が見られた項目の要因確認を、面談の中で優先的に行います。")
    else:
        focus_parts.append("現在の安定した状態を維持しながら、就労に向けた新しい経験の機会を検討します。")

    return {
        "period_start": period_start,
        "period_end": period_end,
        "support_plan_id": plan.id if plan else None,
        "score_summary": score_summary,
        "achievements": "".join(achievements_parts),
        "challenges": "".join(challenges_parts),
        "plan_adjustments": "".join(adjustments_parts),
        "next_period_focus": "".join(focus_parts),
        "model_name": "rule-based",
    }
