"""Google Gemini API 連携（REST API / httpx）。

- 出力はJSONスキーマで検証し、不正な場合は再試行する
- APIキーはコードに記載せず環境変数（GEMINI_API_KEY）から取得する
"""

import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.schemas.ai import AiAnalysisResult, SupportPlanDraft
from app.services.ai.base import AIService, AIServiceError, load_prompt

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_ATTEMPTS = 3


class GeminiAIService(AIService):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise AIServiceError("GEMINI_API_KEY が設定されていません")
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self.name = self._model

    def _call(self, prompt: str) -> str:
        url = GEMINI_ENDPOINT.format(model=self._model)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }
        try:
            response = httpx.post(
                url,
                params={"key": self._api_key},
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # APIキー等の内部情報をメッセージへ含めない
            raise AIServiceError(f"Gemini APIの呼び出しに失敗しました: {type(exc).__name__}") from exc
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise AIServiceError("Gemini APIの応答形式が想定と異なります") from exc

    def _generate_validated[T: BaseModel](self, prompt_file: str, context: dict[str, Any], schema_cls: type[T]) -> T:
        prompt_template, _version = load_prompt(prompt_file)
        prompt = prompt_template.replace(
            "{context_json}", json.dumps(context, ensure_ascii=False, indent=1)
        ).replace(
            "{output_schema}", json.dumps(schema_cls.model_json_schema(), ensure_ascii=False)
        )

        last_error: Exception | None = None
        for _attempt in range(MAX_ATTEMPTS):
            text = self._call(prompt)
            try:
                return schema_cls.model_validate_json(text)
            except ValidationError as exc:
                last_error = exc
                continue
        raise AIServiceError(f"AI出力のJSONスキーマ検証に{MAX_ATTEMPTS}回失敗しました") from last_error

    def analyze_daily(self, context: dict[str, Any]) -> AiAnalysisResult:
        result = self._generate_validated("daily_analysis_prompt.md", context, AiAnalysisResult)
        # 利用者向け提案は最大3件に制限
        result.user_recommendations = result.user_recommendations[:3]
        return result

    def generate_support_plan(self, context: dict[str, Any]) -> SupportPlanDraft:
        return self._generate_validated("support_plan_prompt.md", context, SupportPlanDraft)
