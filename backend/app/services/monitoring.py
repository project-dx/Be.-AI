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


MAX_OVERALL_CHARS = 240  # 200文字程度に収める（超える場合は末尾を丸める）


def _jp_date(d: date) -> str:
    """OSに依存しない日本語の日付表記（例: 2026年7月29日）"""
    return f"{d.year}年{d.month}月{d.day}日"


def build_monitoring_draft(
    db: Session,
    user_id: int,
    period_months: int = 6,
    period_start: date | None = None,
    period_end: date | None = None,
) -> dict[str, Any] | None:
    """期間の実績をまとめた評価の下書きを返す。

    period_start/period_end を渡すとその期間を、渡さない場合は直近 period_months か月を対象にする。
    """
    if period_start is None or period_end is None:
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

    span_days = (period_end - period_start).days + 1
    score_summary: dict[str, Any] = {
        "period_months": period_months,
        "span_days": span_days,
        "report_count": len(reports),
        "score_count": len(scores),
        "staff_report_count": len(staff_reports),
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

    overall = _build_overall_evaluation(
        period_start=period_start,
        period_end=period_end,
        span_days=span_days,
        reports=reports,
        staff_reports=staff_reports,
        improved=improved,
        declined=declined,
        achieved_goals=achieved_goals,
        ongoing_goals=ongoing_goals,
        success_days=success_days,
        urgent_count=urgent_count,
        plan=plan,
    )

    return {
        "period_start": period_start,
        "period_end": period_end,
        "support_plan_id": plan.id if plan else None,
        "score_summary": score_summary,
        "overall_evaluation": overall,
        "achievements": "".join(achievements_parts),
        "challenges": "".join(challenges_parts),
        "plan_adjustments": "".join(adjustments_parts),
        "next_period_focus": "".join(focus_parts),
        "model_name": "rule-based",
    }


def _build_overall_evaluation(
    *,
    period_start: date,
    period_end: date,
    span_days: int,
    reports: list[UserDailyReport],
    staff_reports: list[StaffDailyReport],
    improved: list[str],
    declined: list[str],
    achieved_goals: list[Goal],
    ongoing_goals: list[Goal],
    success_days: int,
    urgent_count: int,
    plan: SupportPlan | None,
) -> str:
    """期間全体をまとめた総合評価を200文字程度で組み立てる。

    個別支援計画の短期目標に対する進み具合を軸に、
    記録量・スコアの推移・次期の方針を1つの短い文章にまとめる。
    断定を避け、スタッフが編集して確定することを前提とした文面にする。
    """
    months = round(span_days / 30, 1)
    parts: list[str] = []

    # 1. 期間と記録量（約45字）
    parts.append(
        f"【{_jp_date(period_start)}〜{_jp_date(period_end)}・約{months}か月】"
        f"日報{len(reports)}件、支援記録{len(staff_reports)}件。"
    )

    # 2. 状態の推移（約35字。スコア名のみを使い簡潔にする）
    def names(items: list[str], limit: int = 2) -> str:
        return "・".join(i.split("（")[0] for i in items[:limit])

    if improved and declined:
        parts.append(f"{names(improved)}は改善、{names(declined)}は低下傾向です。")
    elif improved:
        parts.append(f"{names(improved)}に改善傾向が見られます。")
    elif declined:
        parts.append(f"{names(declined)}に低下傾向があり、要因の確認が必要です。")
    else:
        parts.append("スコアは大きな変動なく安定して推移しました。")

    # 3. 支援計画の短期目標に対する進み具合（約60字）
    if plan and plan.short_term_goals_json:
        goal = str(plan.short_term_goals_json[0]).rstrip("。")
        if declined or urgent_count:
            state = "支援内容の見直しが必要です"
        elif improved or achieved_goals:
            state = "着実に前進しています"
        else:
            state = "継続して取り組んでいます"
        parts.append(f"計画の短期目標「{goal}」は{state}。")
    elif achieved_goals or ongoing_goals:
        parts.append(f"目標は{len(achieved_goals)}件達成、{len(ongoing_goals)}件が継続中です。")

    # 4. 気になる点（あれば約25字）
    if urgent_count:
        parts.append(f"確認・至急対応の記録が{urgent_count}件あり、チームでの共有が必要です。")
    elif success_days:
        parts.append(f"成功体験の記録が{success_days}日分あり、自信につながっています。")

    # 5. 次期に向けて（約45字）
    if declined:
        parts.append("次期は低下項目の要因を面談で確認し、目標を達成しやすい形へ調整します。")
    else:
        parts.append("次期は現在の支援を継続しつつ、本人の希望に応じて次の目標を設定します。")

    text = "".join(parts)
    if len(text) > MAX_OVERALL_CHARS:
        text = text[: MAX_OVERALL_CHARS - 1] + "…"
    return text
