from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    api_url: str = Field(alias="API_URL")
    telegram_allowed_user_id: int = Field(alias="TELEGRAM_ALLOWED_USER_ID")
    api_email: str = Field(alias="API_EMAIL")
    api_password: str = Field(alias="API_PASSWORD")

    bot_mode: Literal["polling", "webhook"] = Field(default="polling", alias="BOT_MODE")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, alias="WEBHOOK_PORT")

    api_timeout_seconds: float = Field(default=15.0, alias="API_TIMEOUT_SECONDS")
    timezone: str = Field(default="America/Sao_Paulo", alias="BOT_TIMEZONE")
    pending_ttl_minutes: int = Field(default=15, alias="PENDING_TTL_MINUTES")

    @field_validator("api_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("telegram_allowed_user_id")
    @classmethod
    def positive_user_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("TELEGRAM_ALLOWED_USER_ID must be a positive integer")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
