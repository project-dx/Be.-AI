from datetime import date
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.schemas.ai import AiAnalysisResult
from app.services.ai.base import AIServiceError
from app.services.ai.mock import MockAIService
from app.services.ai.factory import get_ai_service
from tests.conftest import add_week_reports, login_headers

TODAY = date.today()


def make_context(**overrides):
    context = {
        "period": {"start": "2026-07-01", "end": "2026-07-14"},
        "report_count": 14,
        "daily_reports": [],
        "staff_reports": [{"date": "2026-07-10", "urgency": "normal"}],
        "scores": [],
        "goals": [],
        "stats": {
            "avg_sleep_recent": 7.5,
            "avg_sleep_earlier": 7.5,
            "avg_stress_recent": 2.0,
            "avg_stress_earlier": 2.0,
            "success_experience_days": 4,
            "avg_mood": 4.0,
        },
    }
    context["stats"].update(overrides.pop("stats", {}))
    context.update(overrides)
    return context


def test_mock_short_sleep_generates_sleep_recommendation():
    result = MockAIService().analyze_daily(make_context(stats={"avg_sleep_recent": 5.0}))
    assert any("睡眠" in r.title for r in result.staff_recommendations)
    assert any("就寝" in r.title or "睡眠" in r.title for r in result.user_recommendations)
    assert any("睡眠" in c for c in result.concerns)


def test_mock_high_stress_generates_relief_recommendation():
    result = MockAIService().analyze_daily(make_context(stats={"avg_stress_recent": 4.5}))
    assert any("負担" in r.title for r in result.staff_recommendations)
    assert len(result.risk_flags) >= 1


def test_mock_success_experience_becomes_strength():
    result = MockAIService().analyze_daily(make_context(stats={"success_experience_days": 5}))
    assert any("成功体験" in s for s in result.strengths)


def test_mock_few_records_reports_data_limitation():
    result = MockAIService().analyze_daily(make_context(report_count=3))
    assert any("3日分" in item for item in result.data_limitations)
    assert result.confidence < 0.6


def test_mock_output_varies_with_input():
    """固定文ではなく入力によって結果が変化する"""
    calm = MockAIService().analyze_daily(make_context())
    stressed = MockAIService().analyze_daily(make_context(stats={"avg_stress_recent": 4.8, "avg_sleep_recent": 4.0}))
    assert calm.summary != stressed.summary
    assert calm.concerns != stressed.concerns


def test_mock_user_recommendations_max_3():
    result = MockAIService().analyze_daily(
        make_context(stats={"avg_sleep_recent": 4.0, "avg_stress_recent": 5.0, "success_experience_days": 5})
    )
    assert len(result.user_recommendations) <= 3


def test_mock_result_matches_schema():
    result = MockAIService().analyze_daily(make_context())
    # スキーマ再検証が通ること
    AiAnalysisResult.model_validate(result.model_dump())


def test_mock_support_plan_draft():
    draft = MockAIService().generate_support_plan(make_context(stats={"avg_sleep_recent": 5.0}))
    assert draft.title
    assert any("睡眠" in g for g in draft.short_term_goals)
    assert "下書き" in draft.notes or "スタッフ" in draft.notes


def test_factory_returns_mock_by_default():
    assert isinstance(get_ai_service(), MockAIService)


def test_invalid_json_schema_rejected():
    with pytest.raises(ValidationError):
        AiAnalysisResult.model_validate_json('{"summary": 123, "confidence": "high"}')


def test_gemini_invalid_json_retries_then_fails():
    """AIから不正JSONが返り続けた場合、再試行の後にエラーとなる"""
    from app.services.ai import gemini as gemini_module

    with patch.object(gemini_module.GeminiAIService, "__init__", lambda self: None):
        service = gemini_module.GeminiAIService()
        with patch.object(service, "_call", return_value="これはJSONではありません") as mock_call:
            with pytest.raises(AIServiceError):
                service._generate_validated("daily_analysis_prompt.md", make_context(), AiAnalysisResult)
            assert mock_call.call_count == 3  # 再試行している


def test_api_falls_back_to_mock_on_ai_failure(client, db, staff, member):
    """AI APIが失敗した場合、フォールバックとして安全な結果を返す"""

    class FailingService:
        name = "failing"

        def analyze_daily(self, context):
            raise AIServiceError("接続エラー")

    add_week_reports(db, member.id, TODAY, days=7)
    headers = login_headers(client, "staff@test.com")
    with patch("app.api.ai_analyses.get_ai_service", return_value=FailingService()):
        res = client.post(f"/api/users/{member.id}/ai-analyses", headers=headers,
                          json={"analysis_type": "daily_analysis", "period_days": 14})
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "fallback"
    assert data["result_json"]["summary"]
    assert any("失敗" in item for item in data["result_json"]["data_limitations"])


def test_analysis_requires_reports(client, db, staff, member):
    headers = login_headers(client, "staff@test.com")
    res = client.post(f"/api/users/{member.id}/ai-analyses", headers=headers,
                      json={"analysis_type": "daily_analysis", "period_days": 14})
    assert res.status_code == 422
    assert "日報" in res.json()["detail"]
