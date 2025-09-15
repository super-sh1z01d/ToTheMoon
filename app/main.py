import asyncio
from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.config import settings
from app.api.health import router as health_router
from app.api.tokens import router as tokens_router
from app.api.admin import router as admin_router
from app.api.pages import router as pages_router
from app.api.export import router as export_router
from app.services.pumpportal import run_listener as run_pumpportal_listener
from app.services.scheduler import run_scheduler


def create_app() -> FastAPI:
    configure_logging(settings)
    app = FastAPI(title="ToTheMoon2", version="0.1.0")
    app.include_router(health_router)
    app.include_router(tokens_router)
    app.include_router(admin_router)
    app.include_router(pages_router)
    app.include_router(export_router)
    return app


app = create_app()


@app.on_event("startup")
async def _startup() -> None:
    # Start PumpPortal listener if enabled
    asyncio.create_task(run_pumpportal_listener())
    # Start scheduler loop
    asyncio.create_task(run_scheduler())
