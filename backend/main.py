"""
Emby Stats - 播放统计分析应用
主入口文件
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from routers import stats_router, media_router, auth_router, webhook_router, config_router
from routers.report import router as report_router
from routers.cover import router as cover_router
from routers.auth import get_current_session
from services.scheduler import report_scheduler

# 创建应用实例
app = FastAPI(title="New Emby Stats")

# 启动定时任务调度器
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 确保关键目录存在
    os.makedirs("/config/fonts", exist_ok=True)
    print("✓ 已检查并创建字体目录: /config/fonts")
    
    report_scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    report_scheduler.stop()

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 不需要认证的路径
PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/check",
    "/api/auth/logout",
    "/api/webhook/emby",  # Webhook不需要认证
    "/manifest.json",
    "/sw.js",
}

# 不需要认证的路径前缀
PUBLIC_PREFIXES = [
    "/icons/",
    "/static/",
]


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """认证中间件：保护 API 端点"""
    path = request.url.path

    # 静态资源和认证接口不需要验证
    if path in PUBLIC_PATHS:
        return await call_next(request)

    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return await call_next(request)

    # 前端页面（非 API）不在这里拦截，由前端处理
    if not path.startswith("/api/"):
        return await call_next(request)

    # API 请求需要验证
    session = get_current_session(request)
    if not session:
        return JSONResponse(
            status_code=401,
            content={"detail": "未登录"}
        )

    return await call_next(request)


# 注册路由
app.include_router(auth_router)
app.include_router(stats_router)
app.include_router(media_router)
app.include_router(webhook_router)
app.include_router(config_router)
app.include_router(report_router)
app.include_router(cover_router)

# 静态文件服务
frontend_path = "/app/frontend"
if os.path.exists(frontend_path):
    # PWA 文件路由
    @app.get("/manifest.json")
    async def serve_manifest():
        return FileResponse(
            os.path.join(frontend_path, "manifest.json"),
            media_type="application/manifest+json"
        )

    @app.get("/sw.js")
    async def serve_sw():
        return FileResponse(
            os.path.join(frontend_path, "sw.js"),
            media_type="application/javascript"
        )

    # Icons 目录
    icons_path = os.path.join(frontend_path, "icons")
    if os.path.exists(icons_path):
        app.mount("/icons", StaticFiles(directory=icons_path), name="icons")

    # Static assets (JS, CSS from Vite build)
    static_path = os.path.join(frontend_path, "static")
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    # Catch-all for SPA routing (in case using React Router in the future)
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = os.path.join(frontend_path, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
