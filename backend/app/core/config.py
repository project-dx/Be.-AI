from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定（環境変数 / .env から読み込み）"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Be.カラフル Well-being個別支援AI"
    environment: str = "development"  # development / production
    debug: bool = True

    database_url: str = "sqlite:///./becolorful.db"

    secret_key: str = "dev-only-secret-key-change-me-in-production-0000"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    ai_provider: str = "mock"  # mock / gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 初期管理者（DBにユーザーが1人もいない場合のみ起動時に作成。デプロイ用）
    admin_email: str = ""
    admin_password: str = ""

    @property
    def sqlalchemy_database_url(self) -> str:
        """ホスティング事業者が発行する postgres:// 形式のURLを SQLAlchemy + psycopg 用に正規化する。"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
