from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import check_user_access, get_current_user, require_staff_or_admin
from app.models import AiAnalysis, User
from app.schemas.ai import AiAnalysisOut, AiAnalysisRequest
from app.services.ai.base import AIServiceError
from app.services.ai.context import build_analysis_context, default_period
from app.services.ai.factory import get_ai_service, get_prompt_version
from app.services.ai.mock import MockAIService
from app.services.audit import record_audit

router = APIRouter(prefix="/api/users/{user_id}/ai-analyses", tags=["AI分析"])

# 利用者本人に表示する項目（スタッフ向け情報は含めない）
USER_VISIBLE_KEYS = ["summary", "strengths", "user_recommendations", "data_limitations", "confidence"]


def _filter_for_user(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {k: result.get(k) for k in USER_VISIBLE_KEYS if k in result}


def _visible(analysis: AiAnalysisOut, current_user: User, user_id: int) -> AiAnalysisOut:
    if current_user.role == "user" and current_user.id == user_id:
        analysis.result_json = _filter_for_user(analysis.result_json)
    return analysis


@router.get("", response_model=list[AiAnalysisOut])
def list_analyses(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AiAnalysisOut]:
    check_user_access(db, current_user, user_id)
    rows = (
        db.query(AiAnalysis)
        .filter(AiAnalysis.user_id == user_id)
        .order_by(AiAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_visible(AiAnalysisOut.model_validate(r), current_user, user_id) for r in rows]


@router.post("", response_model=AiAnalysisOut, status_code=status.HTTP_201_CREATED)
def run_analysis(
    user_id: int,
    body: AiAnalysisRequest,
    current_user: User = Depends(require_staff_or_admin),
    db: Session = Depends(get_db),
) -> AiAnalysisOut:
    check_user_access(db, current_user, user_id)
    period_start, period_end = default_period(body.period_days)
    context = build_analysis_context(db, user_id, period_start, period_end)

    if context["report_count"] == 0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="分析対象期間に日報がありません。日報の入力後に実行してください",
        )

    service = get_ai_service()
    analysis_status = "success"
    error_message: str | None = None
    model_name = service.name
    try:
        result = service.analyze_daily(context)
    except AIServiceError as exc:
        # 安全なフォールバック: モックAIによるルールベース結果を返す
        error_message = str(exc)
        analysis_status = "fallback"
        fallback = MockAIService()
        result = fallback.analyze_daily(context)
        result.data_limitations = [
            "AIの呼び出しに失敗したため、ルールベースの参考情報を表示しています"
        ] + result.data_limitations
        model_name = f"{service.name} -> mock(fallback)"

    analysis = AiAnalysis(
        user_id=user_id,
        analysis_date=date.today(),
        analysis_type=body.analysis_type,
        input_period_start=period_start,
        input_period_end=period_end,
        model_name=model_name,
        prompt_version=get_prompt_version("daily_analysis_prompt.md"),
        result_json=result.model_dump(),
        status=analysis_status,
        error_message=error_message,
    )
    db.add(analysis)
    db.flush()
    record_audit(db, current_user.id, "ai_analysis.run", "ai_analysis", analysis.id,
                 {"target_user_id": user_id, "status": analysis_status})
    db.commit()
    db.refresh(analysis)
    return _visible(AiAnalysisOut.model_validate(analysis), current_user, user_id)


@router.get("/{analysis_id}", response_model=AiAnalysisOut)
def get_analysis(
    user_id: int,
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiAnalysisOut:
    check_user_access(db, current_user, user_id)
    analysis = db.get(AiAnalysis, analysis_id)
    if analysis is None or analysis.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="分析結果が見つかりません")
    return _visible(AiAnalysisOut.model_validate(analysis), current_user, user_id)
