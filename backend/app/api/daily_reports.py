from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user
from app.models import User, UserDailyReport
from app.schemas.report import (
    REQUIRED_ON_SUBMIT,
    UserDailyReportCreate,
    UserDailyReportOut,
    UserDailyReportUpdate,
)
from app.services.audit import record_audit
from app.services.risk import evaluate_user_risks
from app.services.scoring import calculate_scores_for_date

router = APIRouter(prefix="/api/users/{user_id}/daily-reports", tags=["利用者日報"])


def _validate_submit(report: UserDailyReport) -> None:
    """確定（下書きでない）日報の必須項目を検証する。"""
    missing = [label for field, label in REQUIRED_ON_SUBMIT if getattr(report, field) is None]
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"次の項目を入力してください: {'、'.join(missing)}（下書き保存なら未入力でも保存できます）",
        )


def _after_submit(db: Session, user_id: int, report_date: date) -> None:
    """確定日報の保存後にスコア計算とリスク判定を行う。"""
    calculate_scores_for_date(db, user_id, report_date)
    db.flush()
    evaluate_user_risks(db, user_id, report_date)


@router.get("", response_model=list[UserDailyReportOut])
def list_reports(
    user_id: int,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    limit: int = Query(default=60, ge=1, le=366),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserDailyReport]:
    check_user_access(db, current_user, user_id)
    query = db.query(UserDailyReport).filter(UserDailyReport.user_id == user_id)
    if current_user.id != user_id:
        # 他者（スタッフ・管理者）には下書きを表示しない
        query = query.filter(UserDailyReport.is_draft.is_(False))
    if date_from:
        query = query.filter(UserDailyReport.report_date >= date_from)
    if date_to:
        query = query.filter(UserDailyReport.report_date <= date_to)
    return query.order_by(UserDailyReport.report_date.desc()).limit(limit).all()


@router.post("", response_model=UserDailyReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    user_id: int,
    body: UserDailyReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserDailyReport:
    check_user_access(db, current_user, user_id)
    if current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="日報は本人のみ入力できます")

    existing = (
        db.query(UserDailyReport)
        .filter(UserDailyReport.user_id == user_id, UserDailyReport.report_date == body.report_date)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="この日付の日報は既に存在します。既存の日報を更新してください",
        )

    report = UserDailyReport(user_id=user_id, **body.model_dump())
    if not report.is_draft:
        _validate_submit(report)
    db.add(report)
    db.flush()
    if not report.is_draft:
        _after_submit(db, user_id, report.report_date)
    record_audit(db, current_user.id, "daily_report.create", "user_daily_report", report.id,
                 {"report_date": body.report_date.isoformat(), "is_draft": report.is_draft})
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}", response_model=UserDailyReportOut)
def get_report(
    user_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserDailyReport:
    check_user_access(db, current_user, user_id)
    report = db.get(UserDailyReport, report_id)
    if report is None or report.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="日報が見つかりません")
    if report.is_draft and current_user.id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="日報が見つかりません")
    return report


@router.patch("/{report_id}", response_model=UserDailyReportOut)
def update_report(
    user_id: int,
    report_id: int,
    body: UserDailyReportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserDailyReport:
    check_user_access(db, current_user, user_id)
    if current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="日報は本人のみ編集できます")
    report = db.get(UserDailyReport, report_id)
    if report is None or report.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="日報が見つかりません")

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(report, key, value)
    if not report.is_draft:
        _validate_submit(report)
        db.flush()
        _after_submit(db, user_id, report.report_date)
    record_audit(db, current_user.id, "daily_report.update", "user_daily_report", report.id,
                 {"is_draft": report.is_draft})
    db.commit()
    db.refresh(report)
    return report
