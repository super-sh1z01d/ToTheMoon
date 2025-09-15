from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    DB_DSN: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/tothemoon2",
        description="Async SQLAlchemy DSN",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG/INFO/WARN/ERROR")


settings = Settings()

