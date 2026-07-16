import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    ai_analyses,
    audit_logs,
    auth,
    daily_reports,
    dashboard,
    goals,
    risks,
    scores,
    staff_reports,
    support_plans,
    system_settings,
    users,
)
from app.core.bootstrap import bootstrap_initial_admin
from app.core.config import get_settings

logger = logging.getLogger("app")

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap_initial_admin()
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    description=(
        "利用者の日報とスタッフの支援記録をAIが分析し、支援判断を補助する参考情報を提供します。"
        "本システムのAI出力は医療診断ではなく、支援スタッフの判断を代替するものではありません。"
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []) if loc not in ("body",))
        errors.append({"field": field, "message": error.get("msg", "")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "入力内容に誤りがあります。入力項目を確認してください", "errors": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # 内部情報をレスポンスへ含めない（詳細はサーバーログのみ）
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "サーバー内部でエラーが発生しました。時間をおいて再度お試しください"},
    )


@app.get("/api/health", tags=["ヘルスチェック"])
def health() -> dict:
    return {"status": "ok", "ai_provider": settings.ai_provider}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(daily_reports.router)
app.include_router(staff_reports.router)
app.include_router(scores.router)
app.include_router(ai_analyses.router)
app.include_router(support_plans.router)
app.include_router(goals.router)
app.include_router(risks.router)
app.include_router(dashboard.router)
app.include_router(dashboard.user_dashboard_router)
app.include_router(audit_logs.router)
app.include_router(system_settings.router)
