"""AI Service configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AI Service settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Google Gemini
    gemini_enabled: bool = Field(default=False, alias="GEMINI_ENABLED")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(
        default="gemini-3.5-flash-lite",
        alias="GEMINI_MODEL",
    )
    gemini_timeout_seconds: float = Field(default=30.0, alias="GEMINI_TIMEOUT_SECONDS")

    # Core Task API
    task_api_url: str = Field(default="http://task-service:8000", alias="TASK_API_URL")
    task_api_timeout: float = Field(default=10.0, alias="TASK_API_TIMEOUT")

    # AI Service
    max_tool_iterations: int = 4
    max_output_tokens: int = 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def use_mock(self) -> bool:
        """Use the deterministic mock unless Gemini is explicitly enabled.

        Enabling Gemini without an API key does not silently fall back to the
        mock: requests return a clear configuration error instead, so a demo
        can never be mistaken for a live model call.
        """
        return not self.gemini_enabled

    @property
    def gemini_configured(self) -> bool:
        return self.gemini_enabled and bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
