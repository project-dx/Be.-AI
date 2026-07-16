from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.schemas.ai import AiAnalysisResult, SupportPlanDraft

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class AIServiceError(Exception):
    """AI呼び出し・検証の失敗"""


def load_prompt(name: str) -> tuple[str, str]:
    """プロンプト本文とバージョンを返す。"""
    path = PROMPTS_DIR / name
    text = path.read_text(encoding="utf-8")
    version = "1.0"
    first_line = text.splitlines()[0] if text else ""
    if "version:" in first_line:
        version = first_line.split("version:")[1].strip(" ->")
    return text, version


class AIService(ABC):
    """AIプロバイダの抽象基底クラス。将来Gemini以外（OpenAI等）へ差し替え可能。"""

    name: str = "base"

    @abstractmethod
    def analyze_daily(self, context: dict[str, Any]) -> AiAnalysisResult:
        """日次分析を実行し、検証済みの結果を返す。"""

    @abstractmethod
    def generate_support_plan(self, context: dict[str, Any]) -> SupportPlanDraft:
        """個別支援計画の下書きを生成する。"""
