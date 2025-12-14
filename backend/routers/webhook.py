"""Webhook路由"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging
import sys

from services.webhook import WebhookService
from services.tmdb import TMDBService
from services.notification import NotificationService, NotificationTemplateService
from config import settings
from config_storage import config_storage

# 配置logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhook", tags=["webhook"])

# 初始化服务
webhook_service = WebhookService()


@router.post("/emby")
async def handle_emby_webhook(request: Request):
    """处理Emby Webhook事件"""
    try:
        # 获取请求体
        data = await request.json()
        event_type = data.get('Event', 'Unknown')
        logger.info(f"收到Emby webhook事件: {event_type}")
        logger.info(f"完整webhook数据: {data}")
        
        # 构建事件上下文
        context = webhook_service.build_event_context(data)
        if not context:
            raise HTTPException(status_code=400, detail="无效的事件数据")
        
        # 从配置文件获取通知配置
        tg_config = config_storage.get_telegram_config()
        wecom_config = config_storage.get_wecom_config()
        discord_config = config_storage.get_discord_config()
        tmdb_config = config_storage.get_tmdb_config()
        
        notification_config = {
            "telegram": {
                "token": tg_config.get("bot_token", ""),
                "admins": tg_config.get("admins", []),
                "users": tg_config.get("users", []),
            },
            "wecom": wecom_config,
            "discord": discord_config
        }
        
        # 初始化通知服务
        notification_service = NotificationService(notification_config)
        templates = config_storage.get_templates()
        template_service = NotificationTemplateService(templates)
        
        # 获取TMDB图片
        image_url = None
        if context.get("item_id"):
            tmdb_service = TMDBService(
                api_key=tmdb_config.get("api_key", ""),
                image_base_url=tmdb_config.get("image_base_url", "https://image.tmdb.org/t/p/original"),
                emby_server=settings.EMBY_URL
            )
            
            # 构建item对象
            item = {
                "Id": context.get("item_id"),
                "Type": context.get("item_type"),
                "Name": context.get("item_name"),
                "SeriesName": context.get("series_name"),
                "ProductionYear": context.get("item_year"),
                "ProviderIds": {
                    "Tmdb": context.get("tmdb_id"),
                    "Imdb": context.get("imdb_id"),
                }
            }
            image_url = tmdb_service.get_image_url(item)
        
        # 确定模板类型
        event = context.get("event", "")
        if event.startswith("playback."):
            template_name = "playback"
        elif event == "library.new":
            template_name = "library"
        elif event in ("user.authenticated", "user.authenticationfailed"):
            template_name = "login"
        elif event.startswith("item.mark") or event.startswith("user.rating") or event.startswith("item.rating") or event.startswith("user.favorite") or event.startswith("item.favorite") or event == "item.rate":
            template_name = "mark"
        else:
            template_name = "default"
        
        # 渲染通知模板
        title, message = template_service.render(template_name, context)
        
        # 发送通知
        await notification_service.send_all(title, message, image_url)
        
        return {"status": "success", "event": context.get("event")}
    
    except Exception as e:
        logger.exception(f"处理webhook时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_notification():
    """测试通知功能"""
    try:
        # 从配置文件获取通知配置
        tg_config = config_storage.get_telegram_config()
        wecom_config = config_storage.get_wecom_config()
        discord_config = config_storage.get_discord_config()
        
        notification_config = {
            "telegram": {
                "token": tg_config.get("bot_token", ""),
                "admins": tg_config.get("admins", []),
                "users": tg_config.get("users", []),
            },
            "wecom": wecom_config,
            "discord": discord_config
        }
        
        notification_service = NotificationService(notification_config)
        await notification_service.send_all(
            title="🧪 测试通知",
            message="这是一条来自 Emby Stats 的测试通知\n如果您收到此消息，说明通知配置正确！",
            image_url=None
        )
        
        return {"status": "success", "message": "测试通知已发送"}
    
    except Exception as e:
        logger.exception(f"测试通知失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
