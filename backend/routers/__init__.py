"""路由模块"""
from .stats import router as stats_router
from .media import router as media_router
from .auth import router as auth_router
from .webhook import router as webhook_router
from .config import router as config_router

__all__ = ["stats_router", "media_router", "auth_router", "webhook_router", "config_router"]
