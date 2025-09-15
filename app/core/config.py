from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    DB_DSN: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/tothemoon2",
        description="Async SQLAlchemy DSN",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG/INFO/WARN/ERROR")
    PUMPPORTAL_WS_URL: str = Field(
        default="wss://pumpportal.fun/data-api/real-time", description="PumpPortal WebSocket URL"
    )
    PUMPPORTAL_ENABLED: bool = Field(default=False, description="Enable PumpPortal WebSocket listener")
    BIRDEYE_API_KEY: str | None = Field(default=None, description="Birdeye API key")
    BIRDEYE_BASE_URL: str = Field(default="https://public-api.birdeye.so", description="Birdeye base URL")
    BIRDEYE_CACHE_TTL: int = Field(default=30, description="Birdeye cache TTL seconds")
    EXT_MAX_CONCURRENCY: int = Field(default=5, description="Max parallel external requests")
    SCHED_INTERVAL_INITIAL_SEC: int = Field(default=30, description="Scheduler interval for Initial tokens")
    SCHED_INTERVAL_ACTIVE_SEC: int = Field(default=30, description="Scheduler interval for Active tokens")
    MIN_ACTIVE_LIQUIDITY: float = Field(default=1000.0, description="Min liquidity to activate token")


settings = Settings()
