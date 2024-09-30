import logging
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class AppSettings(BaseSettings):
    ENV_NAME: str = "default_env"

    DB_NAME: str = "default_db"
    DB_USER: str = "default_user"
    DB_PASS: str = "default_pass"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"

    DB_URL: str = ""

    ELASTIC_PASSWORD: str = "elastic_password"
    ELASTIC_HOST: str = "localhost"
    ELASTIC_PORT: int = 9200

    SQL_SHOW_QUERY: bool = False

    @field_validator("DB_URL", mode="before")
    def get_database_url(cls, v: str | None, info: Any) -> str:
        if isinstance(v, str) and v:
            return v

        values = info.data
        user = values.get("DB_USER")
        password = values.get("DB_PASS")
        host = values.get("DB_HOST")
        port = values.get("DB_PORT")
        db_name = values.get("DB_NAME")

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"

    class Config:
        env_file = "../.env", ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_app_settings() -> AppSettings:
    settings = AppSettings()
    logger.info(f">>> Loading settings for: {settings.ENV_NAME}\n")
    return settings
