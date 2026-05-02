"""アプリケーション設定ファイル"""

from __future__ import annotations

from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """アプリケーション設定クラス"""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini-2025-04-14"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 4000
    LLM_PROVIDER: str = "openai"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEBUG_API_LOG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite:///./survey_analysis.db"
    CACHE_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    ENCRYPTION_KEY: Optional[str] = None

    MAX_CONCURRENT_TASKS: int = 32
    REQUEST_TIMEOUT: int = 15
    MAX_FILE_SIZE: int = 52428800
    OFFLINE_MODE: bool = False

    BATCH_SIZE: int = 50
    BATCH_DELAY: float = 0.1

    CACHE_TTL: int = 3600
    CACHE_MAX_SIZE: int = 1000

    API_TIMEOUT_COMPLETIONS_SEC: int = 10
    API_TIMEOUT_EMOTION_SEC: int = 8
    API_TIMEOUT_MODERATION_SEC: int = 5
    API_MAX_RETRIES: int = 3
    LLM_RETRY_BASE_MS: int = 500

    OPENAI_MAX_INPUT_CHARS: int = 1200

    CIRCUIT_BREAKER_THRESHOLD: int = 3
    CIRCUIT_BREAKER_COOLDOWN_SEC: int = 30

    ENABLE_WEB_RESEARCH: bool = False
    ENABLE_COMPETITIVE_ANALYSIS: bool = True
    ENABLE_CACHING: bool = True
    ENABLE_MONITORING: bool = True
    PDF_ENGINE_PREF: str = "high_quality"
    PDF_AUTO_FALLBACK: bool = False
    MAX_ACTION_ITEMS: int = 10

    PDF_LLM_MODEL: str = "gpt-4.1-mini-2025-04-14"
    USE_HYBRID_SENTIMENT: bool = False

    PDF_PERSPECTIVE_MAX_TOKENS: int = 2000
    PDF_SUMMARY_MAX_TOKENS: int = 2000

    WORDCLOUD_LLM_FILTER: bool = True
    WORDCLOUD_FILTER_MAX_TOKENS_PER_CATEGORY: int = 200

    FAST_PREVIEW_ENABLED: bool = True
    FAST_PREVIEW_SAMPLE_SIZE: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
    )

    @field_validator("OPENAI_API_KEY", mode="before")
    @classmethod
    def _normalize_openai_api_key(cls, value: object) -> str:
        return str(value or "").strip()

    @field_validator("SECRET_KEY", "JWT_SECRET", "ENCRYPTION_KEY", mode="before")
    @classmethod
    def _normalize_optional_secret(cls, value: object) -> Optional[str]:
        normalized = str(value or "").strip()
        return normalized or None

    @staticmethod
    def _is_placeholder_secret(value: Optional[str]) -> bool:
        if value is None:
            return True
        lowered = value.strip().lower()
        return lowered.startswith("your_") or lowered in {"changeme", "change_me", "replace-me"}

    def require_openai_api_key(self) -> str:
        api_key = (self.OPENAI_API_KEY or "").strip()
        if not api_key or api_key.startswith("sk-test"):
            raise ValueError("OPENAI_API_KEY is empty. Set a real key in .env or environment variables.")
        return api_key

    def require_secret(self, field_name: str) -> str:
        if field_name not in {"SECRET_KEY", "JWT_SECRET", "ENCRYPTION_KEY"}:
            raise ValueError(f"Unsupported secret field: {field_name}")
        value = getattr(self, field_name, None)
        if self._is_placeholder_secret(value):
            raise ValueError(f"{field_name} is not configured.")
        return str(value).strip()


settings = AppSettings()
