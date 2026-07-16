from datetime import UTC, datetime, date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user, require_staff_or_admin
from app.models import SupportAction, SupportPlan, SupportPlanVersion, User
from app.schemas.ai import SupportPlanDraft
from app.schemas.plan import (
    SupportActionCreate,
    SupportActionOut,
    SupportPlanCreate,
    SupportPlanOut,
    SupportPlanUpdate,
    SupportPlanVersionOut,
)
from app.services.ai.base import AIServiceError
from app.services.ai.context import build_analysis_context, default_period
from app.services.ai.factory import get_ai_service
from app.services.ai.mock import MockAIService
from app.services.audit import record_audit

router = APIRouter(tags=["個別支援計画"])


def _snapshot(plan: SupportPlan) -> dict:
    return {
        "title": plan.title,
        "status": plan.status,
        "current_issues": plan.current_issues,
        "strengths": plan.strengths,
        "user_preferences": plan.user_preferences,
        "background_hypothesis": plan.background_hypothesis,
        "long_term_goal": plan.long_term_goal,
        "short_term_goals_json": plan.short_term_goals_json,
        "support_methods_json": plan.support_methods_json,
        "home_actions_json": plan.home_actions_json,
        "office_actions_json": plan.office_actions_json,
        "user_actions_json": plan.user_actions_json,
        "evaluation_metrics_json": plan.evaluation_metrics_json,
        "evaluation_date": plan.evaluation_date.isoformat() if plan.evaluation_date else None,
        "next_review_date": plan.next_review_date.isoformat() if plan.next_review_date else None,
        "notes": plan.notes,
    }


def _add_version(db: Session, plan: SupportPlan, changed_by: int, reason: str) -> None:
    latest = (
        db.query(SupportPlanVersion)
        .filter(SupportPlanVersion.support_plan_id == plan.id)
        .order_by(SupportPlanVersion.version_number.desc())
        .first()
    )
    db.add(
        SupportPlanVersion(
            support_plan_id=plan.id,
            version_number=(latest.version_number + 1) if latest else 1,
            snapshot_json=_snapshot(plan),
            changed_by=changed_by,
            change_reason=reason,
        )
    )


def _get_plan_with_access(db: Session, current_user: User, plan_id: int) -> SupportPlan:
    plan = db.get(SupportPlan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="支援計画が見つかりません")
    check_user_access(db, current_user, plan.user_id)
    return plan


@router.get("/api/users/{user_id}/support-plans", response_model=list[SupportPlanOut])
def list_plans(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SupportPlan]:
    check_user_access(db, current_user, user_id)
    query = db.query(SupportPlan).filter(SupportPlan.user_id == user_id)
    if current_user.role == "user":
        # 利用者本人には承認済み以降の計画のみ表示
        query = query.filter(SupportPlan.status.in_(["approved", "active", "evaluated", "closed"]))
    return query.order_by(SupportPlan.updated_at.desc()).all()


@router.post(
    "/api/users/{user_id}/support-plans/generate",
    response_model=SupportPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def generate_plan(
    user_id: int,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> SupportPlan:
    """AIによる個別支援計画の下書き生成。承認されるまで正式な計画にはならない。"""
    check_user_access(db, current_user, user_id)
    period_start, period_end = default_period(30)
    context = build_analysis_context(db, user_id, period_start, period_end)
    if context["report_count"] == 0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="対象期間に日報がないため下書きを生成できません",
        )

    service = get_ai_service()
    try:
        draft: SupportPlanDraft = service.generate_support_plan(context)
    except AIServiceError:
        draft = MockAIService().generate_support_plan(context)
        draft.notes = "AI呼び出しに失敗したため、ルールベースの下書きを表示しています。" + draft.notes

    plan = SupportPlan(
        user_id=user_id,
        title=draft.title,
        status="draft",
        current_issues=draft.current_issues,
        strengths=draft.strengths,
        user_preferences=draft.user_preferences,
        background_hypothesis=draft.background_hypothesis,
        long_term_goal=draft.long_term_goal,
        short_term_goals_json=draft.short_term_goals,
        support_methods_json=draft.support_methods,
        home_actions_json=draft.home_actions,
        office_actions_json=draft.office_actions,
        user_actions_json=draft.user_actions,
        evaluation_metrics_json=draft.evaluation_metrics,
        notes=draft.notes,
        created_by=current_user.id,
    )
    db.add(plan)
    db.flush()
    _add_version(db, plan, current_user.id, "AIによる下書き生成")
    record_audit(db, current_user.id, "support_plan.generate", "support_plan", plan.id,
                 {"target_user_id": user_id})
    db.commit()
    db.refresh(plan)
    return plan


@router.post(
    "/api/users/{user_id}/support-plans",
    response_model=SupportPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(
    user_id: int,
    body: SupportPlanCreate,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> SupportPlan:
    check_user_access(db, current_user, user_id)
    plan = SupportPlan(user_id=user_id, created_by=current_user.id, **body.model_dump())
    db.add(plan)
    db.flush()
    _add_version(db, plan, current_user.id, "新規作成")
    record_audit(db, current_user.id, "support_plan.create", "support_plan", plan.id)
    db.commit()
    db.refresh(plan)
    return plan


@router.patch("/api/support-plans/{plan_id}", response_model=SupportPlanOut)
def update_plan(
    plan_id: int,
    body: SupportPlanUpdate,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> SupportPlan:
    plan = _get_plan_with_access(db, current_user, plan_id)
    data = body.model_dump(exclude_unset=True)
    reason = data.pop("change_reason", None) or "編集"
    if data.get("status") in {"approved"}:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="承認は承認APIから実行してください"
        )
    for key, value in data.items():
        setattr(plan, key, value)
    db.flush()
    _add_version(db, plan, current_user.id, reason)
    record_audit(db, current_user.id, "support_plan.update", "support_plan", plan.id)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/api/support-plans/{plan_id}/approve", response_model=SupportPlanOut)
def approve_plan(
    plan_id: int,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> SupportPlan:
    plan = _get_plan_with_access(db, current_user, plan_id)
    if plan.status not in {"draft", "in_review"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="この状態の計画は承認できません")
    plan.status = "approved"
    plan.approved_by = current_user.id
    plan.approved_at = datetime.now(UTC)
    db.flush()
    _add_version(db, plan, current_user.id, "承認")
    record_audit(db, current_user.id, "support_plan.approve", "support_plan", plan.id)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/api/support-plans/{plan_id}/versions", response_model=list[SupportPlanVersionOut])
def list_versions(
    plan_id: int,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[SupportPlanVersion]:
    _get_plan_with_access(db, current_user, plan_id)
    return (
        db.query(SupportPlanVersion)
        .filter(SupportPlanVersion.support_plan_id == plan_id)
        .order_by(SupportPlanVersion.version_number.desc())
        .all()
    )


# --- 支援実施記録（効果測定） ---


@router.get("/api/users/{user_id}/support-actions", response_model=list[SupportActionOut])
def list_actions(
    user_id: int,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[SupportAction]:
    check_user_access(db, current_user, user_id)
    return (
        db.query(SupportAction)
        .filter(SupportAction.user_id == user_id)
        .order_by(SupportAction.action_date.desc(), SupportAction.id.desc())
        .all()
    )


@router.post(
    "/api/users/{user_id}/support-actions",
    response_model=SupportActionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_action(
    user_id: int,
    body: SupportActionCreate,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> SupportAction:
    check_user_access(db, current_user, user_id)
    if body.support_plan_id is not None:
        plan = db.get(SupportPlan, body.support_plan_id)
        if plan is None or plan.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="支援計画が見つかりません")
    action = SupportAction(user_id=user_id, staff_id=current_user.id, **body.model_dump())
    db.add(action)
    db.flush()
    record_audit(db, current_user.id, "support_action.create", "support_action", action.id)
    db.commit()
    db.refresh(action)
    return action
