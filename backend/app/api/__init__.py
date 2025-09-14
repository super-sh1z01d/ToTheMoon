"""
API routers for ToTheMoon2
"""

from .tokens import router as tokens_router
from .pools import router as pools_router
from .system import router as system_router
from .health import router as health_router
from .websocket import router as websocket_router
from .birdeye import router as birdeye_router
from .scoring import router as scoring_router
from .lifecycle import router as lifecycle_router
from .toml_export import router as toml_export_router
from .celery_management import router as celery_router
from .realtime import router as realtime_router

__all__ = [
    "tokens_router",
    "pools_router",
    "system_router", 
    "health_router",
    "websocket_router",
    "birdeye_router",
    "scoring_router",
    "lifecycle_router",
    "toml_export_router",
    "celery_router",
    "realtime_router"
]
