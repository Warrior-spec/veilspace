from functools import lru_cache
from pathlib import Path
from pydantic import Field, SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VEILSPACE_", env_file=".env", extra="ignore"
    )

    environment: str = "development"
    data_dir: Path = Path("storage")
    session_hours: int = Field(default=24, ge=1, le=720)
    allow_registration: bool = True
    openai_api_key: SecretStr = Field(default=SecretStr(""), validation_alias="OPENAI_API_KEY")
    ai_daily_budget_usd: float = Field(default=1.0, ge=0, le=10)
    worker_enabled: bool = True
    max_upload_bytes: int = Field(default=10485760, ge=1024, le=10485760)


@lru_cache
def get_settings() -> Settings:
    return Settings()
