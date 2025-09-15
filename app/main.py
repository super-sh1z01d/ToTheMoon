from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.config import settings
from app.api.health import router as health_router


def create_app() -> FastAPI:
    configure_logging(settings)
    app = FastAPI(title="ToTheMoon2", version="0.1.0")
    app.include_router(health_router)
    return app


app = create_app()

