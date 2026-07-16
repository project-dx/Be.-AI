from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user, require_admin, require_roles
from app.api.ai_analyses import _filter_for_user
from app.models import (
    AiAnalysis,
    Goal,
    Profile,
    RiskAlert,
    ScoreResult,
    StaffDailyReport,
    SupportPlan,
    User,
    UserDailyReport,
)

router = APIRouter(prefix="/api/dashboard", tags=["ダッシュボード"])

user_dashboard_router = APIRouter(prefix="/api/users/{user_id}/dashboard", tags=["ダッシュボード"])


def _score_to_dict(s: ScoreResult) -> dict[str, Any]:
    return {
        "score_date": s.score_date.isoformat(),
        "life_rhythm_score": s.life_rhythm_score,
        "sleep_score": s.sleep_score,
        "mental_score": s.mental_score,
        "wellbeing_score": s.wellbeing_score,
        "self_efficacy_score": s.self_efficacy_score,
        "work_readiness_score": s.work_readiness_score,
        "stress_status": s.stress_status,
    }


def build_user_dashboard(db: Session, user_id: int, for_role: str) -> dict[str, Any]:
    today = date.today()
    start30 = today - timedelta(days=29)

    scores = (
        db.query(ScoreResult)
        .filter(ScoreResult.user_id == user_id, ScoreResult.score_date >= start30)
        .order_by(ScoreResult.score_date)
        .all()
    )
    reports = (
        db.query(UserDailyReport)
        .filter(
            UserDailyReport.user_id == user_id,
            UserDailyReport.report_date >= start30,
            UserDailyReport.is_draft.is_(False),
        )
        .order_by(UserDailyReport.report_date)
        .all()
    )
    today_report = (
        db.query(UserDailyReport)
        .filter(UserDailyReport.user_id == user_id, UserDailyReport.report_date == today)
        .first()
    )
    goals = (
        db.query(Goal)
        .filter(Goal.user_id == user_id, Goal.status.in_(["active", "achieved"]))
        .order_by(Goal.updated_at.desc())
        .all()
    )
    active_goals = [g for g in goals if g.status == "active"]
    latest_analysis = (
        db.query(AiAnalysis)
        .filter(AiAnalysis.user_id == user_id, AiAnalysis.status.in_(["success", "fallback"]))
        .order_by(AiAnalysis.created_at.desc())
        .first()
    )
    plans = (
        db.query(SupportPlan)
        .filter(SupportPlan.user_id == user_id)
        .order_by(SupportPlan.updated_at.desc())
        .all()
    )
    if for_role == "user":
        plans = [p for p in plans if p.status in {"approved", "active", "evaluated", "closed"}]
    current_plan = plans[0] if plans else None

    # 週別の日報入力率（直近4週）
    input_rates = []
    for week_index in range(3, -1, -1):
        week_end = today - timedelta(days=week_index * 7)
        week_start = week_end - timedelta(days=6)
        count = sum(1 for r in reports if week_start <= r.report_date <= week_end)
        input_rates.append(
            {"label": f"{week_start.month}/{week_start.day}週", "rate": round(count / 7 * 100)}
        )

    analysis_result = latest_analysis.result_json if latest_analysis else None
    if for_role == "user":
        analysis_result = _filter_for_user(analysis_result)

    return {
        "latest_score": _score_to_dict(scores[-1]) if scores else None,
        "score_history": [_score_to_dict(s) for s in scores],
        "sleep_history": [
            {"date": r.report_date.isoformat(), "sleep_hours": r.sleep_hours}
            for r in reports
            if r.sleep_hours is not None
        ],
        "stress_history": [
            {"date": r.report_date.isoformat(), "stress_level": r.stress_level}
            for r in reports
            if r.stress_level is not None
        ],
        "today_report": {
            "exists": today_report is not None,
            "is_draft": today_report.is_draft if today_report else None,
            "report_id": today_report.id if today_report else None,
        },
        "report_rate_30d": round(len(reports) / 30 * 100),
        "input_rates_weekly": input_rates,
        "goals": [
            {"id": g.id, "title": g.title, "status": g.status, "progress": g.progress}
            for g in goals[:5]
        ],
        "goal_achievement_rate": (
            round(sum(g.progress for g in active_goals) / len(active_goals)) if active_goals else None
        ),
        "latest_analysis": (
            {
                "id": latest_analysis.id,
                "created_at": latest_analysis.created_at.isoformat(),
                "status": latest_analysis.status,
                "result": analysis_result,
            }
            if latest_analysis
            else None
        ),
        "support_plan": (
            {
                "id": current_plan.id,
                "title": current_plan.title,
                "status": current_plan.status,
                "next_review_date": (
                    current_plan.next_review_date.isoformat() if current_plan.next_review_date else None
                ),
            }
            if current_plan
            else None
        ),
    }


@router.get("/user")
def user_dashboard(
    current_user: User = Depends(require_roles("user")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return build_user_dashboard(db, current_user.id, for_role="user")


@user_dashboard_router.get("")
def user_dashboard_for_staff(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    check_user_access(db, current_user, user_id)
    role_view = "user" if current_user.id == user_id and current_user.role == "user" else "staff"
    return build_user_dashboard(db, user_id, for_role=role_view)


@router.get("/staff")
def staff_dashboard(
    current_user: User = Depends(require_roles("staff", "admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    today = date.today()
    profiles_query = db.query(Profile).join(User, User.id == Profile.user_id).filter(
        User.role == "user", User.is_active.is_(True)
    )
    if current_user.role == "staff":
        profiles_query = profiles_query.filter(Profile.assigned_staff_id == current_user.id)
    profiles = profiles_query.all()
    user_ids = [p.user_id for p in profiles]

    latest_scores: dict[int, ScoreResult] = {}
    for score in (
        db.query(ScoreResult)
        .filter(ScoreResult.user_id.in_(user_ids or [-1]))
        .order_by(ScoreResult.score_date)
        .all()
    ):
        latest_scores[score.user_id] = score

    last_reports: dict[int, date] = {}
    for report in (
        db.query(UserDailyReport)
        .filter(UserDailyReport.user_id.in_(user_ids or [-1]), UserDailyReport.is_draft.is_(False))
        .order_by(UserDailyReport.report_date)
        .all()
    ):
        last_reports[report.user_id] = report.report_date

    open_alerts = (
        db.query(RiskAlert)
        .filter(RiskAlert.user_id.in_(user_ids or [-1]), RiskAlert.status == "open")
        .order_by(RiskAlert.created_at.desc())
        .all()
    )
    alert_counts: dict[int, int] = {}
    for alert in open_alerts:
        alert_counts[alert.user_id] = alert_counts.get(alert.user_id, 0) + 1

    urgent_reports = (
        db.query(StaffDailyReport)
        .filter(
            StaffDailyReport.user_id.in_(user_ids or [-1]),
            StaffDailyReport.urgency == "urgent",
            StaffDailyReport.report_date >= today - timedelta(days=7),
        )
        .order_by(StaffDailyReport.report_date.desc())
        .all()
    )
    name_by_id = {p.user_id: p.display_name for p in profiles}

    return {
        "summary": {
            "assigned_users": len(user_ids),
            "reported_today": sum(1 for uid in user_ids if last_reports.get(uid) == today),
            "open_alerts": len(open_alerts),
            "urgent_reports_7d": len(urgent_reports),
        },
        "users": [
            {
                "user_id": p.user_id,
                "display_name": p.display_name,
                "last_report_date": last_reports.get(p.user_id).isoformat() if p.user_id in last_reports else None,
                "latest_score": _score_to_dict(latest_scores[p.user_id]) if p.user_id in latest_scores else None,
                "open_alert_count": alert_counts.get(p.user_id, 0),
            }
            for p in profiles
        ],
        "alerts": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "user_name": name_by_id.get(a.user_id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "reason": a.reason,
                "created_at": a.created_at.isoformat(),
            }
            for a in open_alerts[:20]
        ],
        "urgent_reports": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_name": name_by_id.get(r.user_id),
                "report_date": r.report_date.isoformat(),
                "support_content": r.support_content,
            }
            for r in urgent_reports
        ],
    }


@router.get("/admin")
def admin_dashboard(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    today = date.today()
    users = db.query(User).all()
    active_members = [u for u in users if u.role == "user" and u.is_active]
    member_ids = [u.id for u in active_members]

    reported_today = (
        db.query(UserDailyReport)
        .filter(
            UserDailyReport.user_id.in_(member_ids or [-1]),
            UserDailyReport.report_date == today,
            UserDailyReport.is_draft.is_(False),
        )
        .count()
    )
    open_alerts = (
        db.query(RiskAlert).filter(RiskAlert.status == "open").order_by(RiskAlert.created_at.desc()).all()
    )
    urgent_reports_7d = (
        db.query(StaffDailyReport)
        .filter(
            StaffDailyReport.urgency == "urgent",
            StaffDailyReport.report_date >= today - timedelta(days=7),
        )
        .count()
    )
    profiles = db.query(Profile).filter(Profile.user_id.in_(member_ids or [-1])).all()
    name_by_id = {p.user_id: p.display_name for p in profiles}

    # 直近14日の日報入力率推移
    input_trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        count = (
            db.query(UserDailyReport)
            .filter(
                UserDailyReport.user_id.in_(member_ids or [-1]),
                UserDailyReport.report_date == d,
                UserDailyReport.is_draft.is_(False),
            )
            .count()
        )
        rate = round(count / len(member_ids) * 100) if member_ids else 0
        input_trend.append({"date": d.isoformat(), "rate": rate})

    plan_counts: dict[str, int] = {}
    for plan in db.query(SupportPlan).all():
        plan_counts[plan.status] = plan_counts.get(plan.status, 0) + 1

    return {
        "summary": {
            "total_users": len(active_members),
            "total_staff": sum(1 for u in users if u.role == "staff" and u.is_active),
            "reported_today": reported_today,
            "report_rate_today": round(reported_today / len(member_ids) * 100) if member_ids else 0,
            "open_alerts": len(open_alerts),
            "urgent_reports_7d": urgent_reports_7d,
        },
        "input_rate_trend": input_trend,
        "plan_status_counts": plan_counts,
        "alerts": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "user_name": name_by_id.get(a.user_id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "reason": a.reason,
                "created_at": a.created_at.isoformat(),
            }
            for a in open_alerts[:20]
        ],
    }
