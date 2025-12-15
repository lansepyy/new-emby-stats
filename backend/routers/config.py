"""配置管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from config_storage import config_storage
from services.scheduler import report_scheduler
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/config", tags=["config"])


class TelegramConfig(BaseModel):
    bot_token: str = ""
    admins: List[int] = []
    users: List[int] = []


class WecomConfig(BaseModel):
    corp_id: str = ""
    secret: str = ""
    agent_id: str = ""
    proxy_url: str = "https://qyapi.weixin.qq.com"
    to_user: str = "@all"


class DiscordConfig(BaseModel):
    webhook_url: str = ""
    username: str = "Emby通知"
    avatar_url: str = ""


class OneBotConfig(BaseModel):
    http_url: str = ""
    access_token: str = ""
    group_ids: List[int] = []
    user_ids: List[int] = []


class TMDBConfig(BaseModel):
    api_key: str = ""
    image_base_url: str = "https://image.tmdb.org/t/p/original"


class ReportChannels(BaseModel):
    telegram: bool = True
    wecom: bool = False
    discord: bool = False
    onebot: bool = False


class ReportConfig(BaseModel):
    enabled: bool = False
    daily_enabled: bool = False
    weekly_enabled: bool = False
    monthly_enabled: bool = False
    daily_time: str = "21:00"
    weekly_time: str = "21:00"
    weekly_day: int = 0
    monthly_time: str = "21:00"
    monthly_day: int = 1
    channels: ReportChannels = ReportChannels()


class NotificationConfig(BaseModel):
    telegram: TelegramConfig = TelegramConfig()
    wecom: WecomConfig = WecomConfig()
    discord: DiscordConfig = DiscordConfig()
    onebot: OneBotConfig = OneBotConfig()
    tmdb: TMDBConfig = TMDBConfig()
    report: ReportConfig = ReportConfig()


class NotificationTemplates(BaseModel):
    templates: Dict[str, Dict[str, str]]


@router.get("/notification")
async def get_notification_config() -> NotificationConfig:
    """获取通知配置"""
    try:
        tg_config = config_storage.get_telegram_config()
        wecom_config = config_storage.get_wecom_config()
        discord_config = config_storage.get_discord_config()
        onebot_config = config_storage.get("onebot", {})
        tmdb_config = config_storage.get_tmdb_config()
        report_config = config_storage.get_report_config()
        
        return NotificationConfig(
            telegram=TelegramConfig(**tg_config),
            wecom=WecomConfig(**wecom_config),
            discord=DiscordConfig(**discord_config),
            onebot=OneBotConfig(**onebot_config),
            tmdb=TMDBConfig(**tmdb_config),
            report=ReportConfig(**report_config)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notification")
async def save_notification_config(config: NotificationConfig):
    """保存通知配置"""
    try:
        # 保存各部分配置
        config_storage.update_section("telegram", config.telegram.dict())
        config_storage.update_section("wecom", config.wecom.dict())
        config_storage.update_section("discord", config.discord.dict())
        config_storage.update_section("onebot", config.onebot.dict())
        config_storage.update_section("tmdb", config.tmdb.dict())
        config_storage.update_section("report", config.report.dict())
        
        # 重新加载定时任务
        report_scheduler.reload_tasks()
        
        return {"status": "success", "message": "配置已保存并立即生效"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification/templates")
async def get_notification_templates() -> NotificationTemplates:
    """获取通知模板配置"""
    templates = config_storage.get_templates()
    return NotificationTemplates(templates=templates)


@router.post("/notification/templates")
async def save_notification_templates(templates: NotificationTemplates):
    """保存通知模板配置"""
    try:
        config_storage.update_section("templates", templates.templates)
        return {"status": "success", "message": "模板已保存并立即生效"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 服务器管理 ====================

class ServerConfig(BaseModel):
    name: str
    emby_url: str
    playback_db: Optional[str] = None
    users_db: Optional[str] = None
    auth_db: Optional[str] = None
    emby_api_key: Optional[str] = None
    is_default: bool = False


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    emby_url: Optional[str] = None
    playback_db: Optional[str] = None
    users_db: Optional[str] = None
    auth_db: Optional[str] = None
    emby_api_key: Optional[str] = None
    is_default: Optional[bool] = None


@router.get("/servers")
async def get_servers():
    """获取所有服务器配置"""
    try:
        servers = config_storage.get("servers", {})
        server_list = []
        for server_id, server_data in servers.items():
            server_list.append({
                "id": server_id,
                **server_data
            })
        # 按创建时间排序
        server_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"servers": server_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers")
async def create_server(server: ServerConfig):
    """创建新服务器配置"""
    try:
        servers = config_storage.get("servers", {})
        
        # 如果设置为默认服务器，取消其他服务器的默认状态
        if server.is_default:
            for s in servers.values():
                s["is_default"] = False
        
        # 生成唯一ID
        server_id = str(uuid.uuid4())
        
        # 保存服务器配置
        server_data = server.dict()
        server_data["created_at"] = datetime.now().isoformat()
        servers[server_id] = server_data
        
        config_storage.update_section("servers", servers)
        
        return {"server_id": server_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/servers/{server_id}")
async def update_server(server_id: str, server: ServerUpdate):
    """更新服务器配置"""
    try:
        servers = config_storage.get("servers", {})
        
        if server_id not in servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        # 如果设置为默认服务器，取消其他服务器的默认状态
        if server.is_default:
            for s in servers.values():
                s["is_default"] = False
        
        # 更新服务器配置（只更新提供的字段）
        update_data = server.dict(exclude_unset=True)
        servers[server_id].update(update_data)
        
        config_storage.update_section("servers", servers)
        
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/servers/{server_id}")
async def delete_server(server_id: str):
    """删除服务器配置"""
    try:
        servers = config_storage.get("servers", {})
        
        if server_id not in servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        # 删除服务器
        del servers[server_id]
        
        # 如果没有默认服务器了，设置第一个为默认
        if servers and not any(s.get("is_default") for s in servers.values()):
            first_server = next(iter(servers.values()))
            first_server["is_default"] = True
        
        config_storage.update_section("servers", servers)
        
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 文件浏览 ====================

@router.get("/browse")
async def browse_files(path: str = "/"):
    """浏览容器内文件系统"""
    try:
        # 安全检查：防止路径遍历攻击
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="路径不存在")
        
        if not os.path.isdir(path):
            raise HTTPException(status_code=400, detail="不是目录")
        
        files = []
        try:
            entries = os.listdir(path)
            for entry in sorted(entries):
                entry_path = os.path.join(path, entry)
                try:
                    is_dir = os.path.isdir(entry_path)
                    stat = os.stat(entry_path)
                    
                    files.append({
                        "name": entry,
                        "path": entry_path,
                        "type": "directory" if is_dir else "file",
                        "size": stat.st_size if not is_dir else 0
                    })
                except (PermissionError, OSError):
                    # 跳过无权限访问的文件
                    continue
        except PermissionError:
            raise HTTPException(status_code=403, detail="无权限访问此目录")
        
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
