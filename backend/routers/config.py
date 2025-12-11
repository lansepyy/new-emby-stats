"""配置管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from config_storage import config_storage

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


class TMDBConfig(BaseModel):
    api_key: str = ""
    image_base_url: str = "https://image.tmdb.org/t/p/original"


class NotificationConfig(BaseModel):
    telegram: TelegramConfig = TelegramConfig()
    wecom: WecomConfig = WecomConfig()
    discord: DiscordConfig = DiscordConfig()
    tmdb: TMDBConfig = TMDBConfig()


class NotificationTemplates(BaseModel):
    templates: Dict[str, Dict[str, str]]


@router.get("/notification")
async def get_notification_config() -> NotificationConfig:
    """获取通知配置"""
    try:
        tg_config = config_storage.get_telegram_config()
        wecom_config = config_storage.get_wecom_config()
        discord_config = config_storage.get_discord_config()
        tmdb_config = config_storage.get_tmdb_config()
        
        return NotificationConfig(
            telegram=TelegramConfig(**tg_config),
            wecom=WecomConfig(**wecom_config),
            discord=DiscordConfig(**discord_config),
            tmdb=TMDBConfig(**tmdb_config)
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
        config_storage.update_section("tmdb", config.tmdb.dict())
        
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
