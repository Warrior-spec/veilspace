from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VEILSPACE_", env_file=".env", extra="ignore"
    )

    environment: str = "development"
    data_dir: Path = Path("storage")


@lru_cache
def get_settings() -> Settings:
    return Settings()
