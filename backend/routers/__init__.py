"""路由模块"""
from .stats import router as stats_router
from .media import router as media_router
from .auth import router as auth_router
from .notifications import router as notifications_router

__all__ = ["stats_router", "media_router", "auth_router", "notifications_router"]
