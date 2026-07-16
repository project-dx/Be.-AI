from app.core.config import get_settings
from app.services.ai.base import AIService, load_prompt
from app.services.ai.gemini import GeminiAIService
from app.services.ai.mock import MockAIService


def get_ai_service() -> AIService:
    """環境変数 AI_PROVIDER に応じてAIサービスを返す（mock / gemini）。"""
    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        return GeminiAIService()
    return MockAIService()


def get_prompt_version(prompt_file: str) -> str:
    _, version = load_prompt(prompt_file)
    return version
