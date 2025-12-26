"""
认证相关路由模块
处理用户登录、登出和会话验证
"""
import secrets
import time
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from services.emby import emby_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 简单的会话存储（内存中）
# 生产环境可考虑使用 Redis
sessions: dict[str, dict] = {}

# 会话有效期（秒）- 7 天
SESSION_EXPIRE = 7 * 24 * 60 * 60


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    username: str | None = None
    message: str | None = None


def clean_expired_sessions():
    """清理过期会话"""
    now = time.time()
    expired = [k for k, v in sessions.items() if v.get("expires", 0) < now]
    for k in expired:
        del sessions[k]


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """用户登录（仅限管理员）"""
    # 清理过期会话
    clean_expired_sessions()

    # 验证用户
    user_info = await emby_service.authenticate_user(
        request.username, request.password
    )

    if not user_info:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 检查是否是管理员
    if not user_info.get("is_admin"):
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    # 创建会话
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "user_id": user_info["user_id"],
        "username": user_info["username"],
        "is_admin": user_info["is_admin"],
        "expires": time.time() + SESSION_EXPIRE
    }

    # 设置 cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=SESSION_EXPIRE,
        samesite="lax"
    )

    return LoginResponse(success=True, username=user_info["username"])


@router.post("/logout")
async def logout(request: Request, response: Response):
    """用户登出"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response.delete_cookie("session_id")
    return {"success": True}


@router.get("/check")
async def check_auth(request: Request):
    """检查登录状态"""
    session_id = request.cookies.get("session_id")

    if not session_id or session_id not in sessions:
        return {"authenticated": False}

    session = sessions[session_id]

    # 检查是否过期
    if session.get("expires", 0) < time.time():
        del sessions[session_id]
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": session.get("username")
    }


def get_current_session(request: Request) -> dict | None:
    """获取当前会话（供中间件使用）"""
    session_id = request.cookies.get("session_id")

    if not session_id or session_id not in sessions:
        return None

    session = sessions[session_id]

    if session.get("expires", 0) < time.time():
        del sessions[session_id]
        return None

    return session
