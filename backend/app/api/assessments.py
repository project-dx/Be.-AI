from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user, require_staff_or_admin
from app.models import Assessment, ColorfulPyramid, MonitoringEvaluation, User
from app.schemas.assessment import (
    AssessmentOut,
    AssessmentUpsert,
    MonitoringGenerateRequest,
    MonitoringOut,
    MonitoringUpdate,
    PyramidOut,
    PyramidUpsert,
)
from app.services.audit import record_audit
from app.services.monitoring import build_monitoring_draft

router = APIRouter(prefix="/api/users/{user_id}", tags=["アセスメント・モニタリング"])


# ============ 初期アセスメント ============
@router.get("/assessment", response_model=AssessmentOut)
def get_assessment(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentOut:
    check_user_access(db, current_user, user_id)
    row = db.query(Assessment).filter(Assessment.user_id == user_id).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="アセスメントはまだ登録されていません")
    return AssessmentOut.model_validate(row)


@router.put("/assessment", response_model=AssessmentOut)
def upsert_assessment(
    user_id: int,
    body: AssessmentUpsert,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> AssessmentOut:
    check_user_access(db, current_user, user_id)
    row = db.query(Assessment).filter(Assessment.user_id == user_id).first()
    data = body.model_dump(exclude_unset=True)
    assessment_date = data.pop("assessment_date", None) or date.today()

    if row is None:
        row = Assessment(user_id=user_id, assessment_date=assessment_date, created_by=current_user.id, **data)
        db.add(row)
        action = "assessment.create"
    else:
        row.assessment_date = assessment_date
        for key, value in data.items():
            setattr(row, key, value)
        action = "assessment.update"

    db.flush()
    record_audit(db, current_user.id, action, "assessment", row.id, {"target_user_id": user_id})
    db.commit()
    db.refresh(row)
    return AssessmentOut.model_validate(row)


# ============ カラフルピラミッド ============
@router.get("/pyramid", response_model=PyramidOut)
def get_pyramid(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PyramidOut:
    check_user_access(db, current_user, user_id)
    row = db.query(ColorfulPyramid).filter(ColorfulPyramid.user_id == user_id).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="カラフルピラミッドはまだ登録されていません")
    return PyramidOut.model_validate(row)


@router.put("/pyramid", response_model=PyramidOut)
def upsert_pyramid(
    user_id: int,
    body: PyramidUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PyramidOut:
    """利用者本人も編集できる（自分の夢・価値観を自分の言葉で書くため）。"""
    check_user_access(db, current_user, user_id)
    row = db.query(ColorfulPyramid).filter(ColorfulPyramid.user_id == user_id).first()
    data = body.model_dump(exclude_unset=True)

    if row is None:
        row = ColorfulPyramid(user_id=user_id, updated_by=current_user.id, **data)
        db.add(row)
        action = "pyramid.create"
    else:
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = current_user.id
        action = "pyramid.update"

    db.flush()
    record_audit(db, current_user.id, action, "pyramid", row.id, {"target_user_id": user_id})
    db.commit()
    db.refresh(row)
    return PyramidOut.model_validate(row)


# ============ モニタリング評価 ============
@router.get("/monitoring-evaluations", response_model=list[MonitoringOut])
def list_monitoring(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MonitoringOut]:
    check_user_access(db, current_user, user_id)
    rows = (
        db.query(MonitoringEvaluation)
        .filter(MonitoringEvaluation.user_id == user_id)
        .order_by(MonitoringEvaluation.evaluation_date.desc())
        .limit(limit)
        .all()
    )
    return [MonitoringOut.model_validate(r) for r in rows]


@router.post("/monitoring-evaluations", response_model=MonitoringOut, status_code=status.HTTP_201_CREATED)
def generate_monitoring(
    user_id: int,
    body: MonitoringGenerateRequest,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> MonitoringOut:
    """期間のスコア・記録から評価の下書きを生成する（スタッフが編集して確定する）。"""
    check_user_access(db, current_user, user_id)
    draft = build_monitoring_draft(db, user_id, body.period_months)
    if draft is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="対象期間に日報がありません。記録の入力後に実行してください",
        )

    row = MonitoringEvaluation(
        user_id=user_id,
        support_plan_id=draft["support_plan_id"],
        evaluation_date=date.today(),
        period_start=draft["period_start"],
        period_end=draft["period_end"],
        score_summary_json=draft["score_summary"],
        achievements=draft["achievements"],
        challenges=draft["challenges"],
        plan_adjustments=draft["plan_adjustments"],
        next_period_focus=draft["next_period_focus"],
        ai_generated=True,
        model_name=draft["model_name"],
        created_by=current_user.id,
    )
    db.add(row)
    db.flush()
    record_audit(db, current_user.id, "monitoring.generate", "monitoring_evaluation", row.id,
                 {"target_user_id": user_id, "period_months": body.period_months})
    db.commit()
    db.refresh(row)
    return MonitoringOut.model_validate(row)


@router.patch("/monitoring-evaluations/{evaluation_id}", response_model=MonitoringOut)
def update_monitoring(
    user_id: int,
    evaluation_id: int,
    body: MonitoringUpdate,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> MonitoringOut:
    check_user_access(db, current_user, user_id)
    row = db.get(MonitoringEvaluation, evaluation_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="モニタリング評価が見つかりません")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    record_audit(db, current_user.id, "monitoring.update", "monitoring_evaluation", row.id,
                 {"target_user_id": user_id})
    db.commit()
    db.refresh(row)
    return MonitoringOut.model_validate(row)
