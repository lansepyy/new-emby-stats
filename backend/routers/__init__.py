"""路由模块"""
from .stats import router as stats_router
from .media import router as media_router
from .auth import router as auth_router
from .notification_templates import router as notification_templates_router

__all__ = ["stats_router", "media_router", "auth_router", "notification_templates_router"]
