from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_db_url(url: str) -> str:
    """Pin the psycopg2 driver.

    A bare ``postgresql://`` URL picks different drivers depending on the
    SQLAlchemy version (psycopg2 in 2.0, psycopg3 in 2.1+), so be explicit.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/inventory"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def _pin_driver(cls, v: str) -> str:
        return normalize_db_url(v)


settings = Settings()
