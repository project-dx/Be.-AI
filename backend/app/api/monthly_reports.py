from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_admin
from app.models import MonthlyReport, User
from app.schemas.ai import MonthlyReportOut, MonthlyReportRequest
from app.services.ai.base import AIServiceError
from app.services.ai.factory import get_ai_service, get_prompt_version
from app.services.ai.mock import MockAIService
from app.services.ai.monthly import build_monthly_data, month_period
from app.services.audit import record_audit

router = APIRouter(prefix="/api/monthly-reports", tags=["月次レポート"])


def _attach_names(report: MonthlyReportOut) -> MonthlyReportOut:
    """result_jsonの利用者別分析へ表示名を付与する（AIには渡していないためここで補完）。"""
    names = (report.facts_json or {}).get("user_names", {})
    if report.result_json and "user_analyses" in report.result_json:
        for ua in report.result_json["user_analyses"]:
            ua["display_name"] = names.get(str(ua.get("user_id")), f"利用者#{ua.get('user_id')}")
    return report


@router.get("", response_model=list[MonthlyReportOut])
def list_reports(
    limit: int = Query(default=12, ge=1, le=50),
    _: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> list[MonthlyReportOut]:
    rows = db.query(MonthlyReport).order_by(MonthlyReport.created_at.desc()).limit(limit).all()
    return [_attach_names(MonthlyReportOut.model_validate(r)) for r in rows]


@router.get("/latest", response_model=MonthlyReportOut)
def get_latest_for_month(
    year_month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    _: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> MonthlyReportOut:
    row = (
        db.query(MonthlyReport)
        .filter(MonthlyReport.year_month == year_month)
        .order_by(MonthlyReport.created_at.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="この月のレポートはまだ生成されていません")
    return _attach_names(MonthlyReportOut.model_validate(row))


@router.post("", response_model=MonthlyReportOut, status_code=status.HTTP_201_CREATED)
def generate_report(
    body: MonthlyReportRequest,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> MonthlyReportOut:
    period_start, period_end = month_period(body.year_month)
    if period_start > date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="未来の月は指定できません")

    facts, ai_context = build_monthly_data(db, period_start, period_end)
    if facts["total_users"] == 0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="この期間に日報・支援記録のある利用者がいません。記録の入力後に実行してください",
        )

    service = get_ai_service()
    report_status = "success"
    error_message: str | None = None
    model_name = service.name
    try:
        result = service.generate_monthly_report(ai_context)
    except AIServiceError as exc:
        error_message = str(exc)
        report_status = "fallback"
        result = MockAIService().generate_monthly_report(ai_context)
        result.data_limitations = [
            "AIの呼び出しに失敗したため、ルールベースの参考情報を表示しています"
        ] + result.data_limitations
        model_name = f"{service.name} -> mock(fallback)"

    report = MonthlyReport(
        year_month=body.year_month,
        period_start=period_start,
        period_end=period_end,
        model_name=model_name,
        prompt_version=get_prompt_version("monthly_report_prompt.md"),
        facts_json=facts,
        result_json=result.model_dump(),
        status=report_status,
        error_message=error_message,
        created_by=current_user.id,
    )
    db.add(report)
    db.flush()
    record_audit(db, current_user.id, "monthly_report.generate", "monthly_report", report.id,
                 {"year_month": body.year_month, "status": report_status})
    db.commit()
    db.refresh(report)
    return _attach_names(MonthlyReportOut.model_validate(report))
