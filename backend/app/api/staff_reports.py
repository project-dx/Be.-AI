from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, require_staff_or_admin
from app.models import Profile, StaffDailyReport, User
from app.schemas.report import (
    URGENCY_PATTERN,
    StaffDailyReportCreate,
    StaffDailyReportOut,
    StaffDailyReportUpdate,
)
from app.services.audit import record_audit
from app.services.risk import evaluate_staff_report_risk

router = APIRouter(prefix="/api/users/{user_id}/staff-reports", tags=["スタッフ日報"])


def _to_out(db: Session, report: StaffDailyReport) -> StaffDailyReportOut:
    out = StaffDailyReportOut.model_validate(report)
    profile = db.query(Profile).filter(Profile.user_id == report.staff_id).first()
    staff = db.get(User, report.staff_id)
    out.staff_name = profile.display_name if profile else (staff.email if staff else None)
    return out


@router.get("", response_model=list[StaffDailyReportOut])
def list_staff_reports(
    user_id: int,
    limit: int = Query(default=60, ge=1, le=366),
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[StaffDailyReportOut]:
    check_user_access(db, current_user, user_id)
    reports = (
        db.query(StaffDailyReport)
        .filter(StaffDailyReport.user_id == user_id)
        .order_by(StaffDailyReport.report_date.desc(), StaffDailyReport.id.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(db, r) for r in reports]


@router.post("", response_model=StaffDailyReportOut, status_code=status.HTTP_201_CREATED)
def create_staff_report(
    user_id: int,
    body: StaffDailyReportCreate,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> StaffDailyReportOut:
    check_user_access(db, current_user, user_id)
    report = StaffDailyReport(user_id=user_id, staff_id=current_user.id, **body.model_dump())
    db.add(report)
    db.flush()
    # 緊急度「至急」はリスクアラートを自動生成
    evaluate_staff_report_risk(db, report)
    record_audit(db, current_user.id, "staff_report.create", "staff_daily_report", report.id,
                 {"target_user_id": user_id, "urgency": report.urgency})
    db.commit()
    db.refresh(report)
    return _to_out(db, report)


@router.patch("/{report_id}", response_model=StaffDailyReportOut)
def update_staff_report(
    user_id: int,
    report_id: int,
    body: StaffDailyReportUpdate,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> StaffDailyReportOut:
    check_user_access(db, current_user, user_id)
    report = db.get(StaffDailyReport, report_id)
    if report is None or report.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="スタッフ日報が見つかりません")
    if current_user.role != "admin" and report.staff_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="記録したスタッフのみ編集できます")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(report, key, value)
    db.flush()
    evaluate_staff_report_risk(db, report)
    record_audit(db, current_user.id, "staff_report.update", "staff_daily_report", report.id)
    db.commit()
    db.refresh(report)
    return _to_out(db, report)


# --- 全利用者を横断したスタッフ日報の一覧（左メニュー「スタッフ日報」用） ---
all_reports_router = APIRouter(prefix="/api/staff-reports", tags=["スタッフ日報"])


@all_reports_router.get("", response_model=list[StaffDailyReportOut])
def list_all_staff_reports(
    urgency: str | None = Query(default=None, pattern=URGENCY_PATTERN),
    user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[StaffDailyReportOut]:
    """管理者は全件、スタッフは担当利用者の記録のみを返す。"""
    query = db.query(StaffDailyReport)

    if current_user.role == "staff":
        assigned_ids = [
            p.user_id
            for p in db.query(Profile).filter(Profile.assigned_staff_id == current_user.id).all()
        ]
        query = query.filter(StaffDailyReport.user_id.in_(assigned_ids or [-1]))

    if user_id is not None:
        check_user_access(db, current_user, user_id)
        query = query.filter(StaffDailyReport.user_id == user_id)
    if urgency:
        query = query.filter(StaffDailyReport.urgency == urgency)

    reports = (
        query.order_by(StaffDailyReport.report_date.desc(), StaffDailyReport.id.desc())
        .limit(limit)
        .all()
    )

    # 利用者名・スタッフ名をまとめて引く（N+1を避ける）
    profiles = db.query(Profile).all()
    name_by_user_id = {p.user_id: p.display_name for p in profiles}

    result = []
    for r in reports:
        out = StaffDailyReportOut.model_validate(r)
        out.staff_name = name_by_user_id.get(r.staff_id)
        out.user_name = name_by_user_id.get(r.user_id)
        result.append(out)
    return result
