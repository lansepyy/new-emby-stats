"""
通知相关路由模块
处理通知设置、模板管理等 API 端点
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks
from pydantic import BaseModel
import logging

from notification_settings import notification_settings_store
from services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class SettingsUpdateRequest(BaseModel):
    """设置更新请求"""
    enabled: Optional[bool] = None
    debug: Optional[bool] = None
    emby_connection: Optional[Dict[str, Any]] = None
    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_admins: Optional[list] = None
    telegram_users: Optional[list] = None
    discord_enabled: Optional[bool] = None
    discord_webhooks: Optional[list] = None
    wecom_enabled: Optional[bool] = None
    wecom_config: Optional[Dict[str, Any]] = None
    tmdb_enabled: Optional[bool] = None
    tmdb_config: Optional[Dict[str, Any]] = None


class TemplateRequest(BaseModel):
    """模板更新请求"""
    title: str
    text: str
    image_template: Optional[str] = None


class TemplatePreviewRequest(BaseModel):
    """模板预览请求"""
    template_id: str
    content: Dict[str, Any]


@router.get("")
async def get_notifications():
    """获取通知配置（包含设置、模板等）"""
    try:
        settings = notification_settings_store.get_settings()
        templates = notification_settings_store.get_templates()
        
        # 转换模板为前端期望的格式
        template_list = []
        for template_id, template_data in templates.items():
            template_list.append({
                "id": template_id,
                "name": template_id.capitalize(),
                "subject": template_data.get("title", ""),
                "body": template_data.get("text", ""),
                "template_type": template_id,
                "variables": [],
            })
        
        # 从设置中提取通道配置
        config = {
            "emby": {
                "enabled": False,
                "server_url": settings.emby_connection.url if settings.emby_connection else None,
                "api_token": settings.emby_connection.api_key if settings.emby_connection else None,
            },
            "telegram": {
                "enabled": settings.telegram_enabled,
                "bot_token": settings.telegram_bot_token,
                "admin_users": [admin.user_id for admin in settings.telegram_admins] if settings.telegram_admins else [],
                "regular_users": [user.user_id for user in settings.telegram_users] if settings.telegram_users else [],
            },
            "discord": {
                "enabled": settings.discord_enabled,
                "webhook_url": settings.discord_webhooks[0].url if settings.discord_webhooks and len(settings.discord_webhooks) > 0 else None,
                "username": settings.discord_webhooks[0].username if settings.discord_webhooks and len(settings.discord_webhooks) > 0 else None,
            },
            "wecom": {
                "enabled": settings.wecom_enabled,
                "corp_id": settings.wecom_config.corp_id if settings.wecom_config else None,
                "corp_secret": settings.wecom_config.corp_secret if settings.wecom_config else None,
                "agent_id": settings.wecom_config.agent_id if settings.wecom_config else None,
                "proxy_url": settings.wecom_config.proxy if settings.wecom_config else None,
                "user_list": [settings.wecom_config.to_user] if settings.wecom_config and settings.wecom_config.to_user else [],
            },
            "tmdb": {
                "enabled": settings.tmdb_enabled,
                "api_key": settings.tmdb_config.api_key if settings.tmdb_config else None,
            }
        }
        
        return {
            "settings": [],
            "templates": template_list,
            "config": config,
            "history": []
        }
    except Exception as e:
        logger.error(f"[Notifications] 获取通知数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取通知数据失败: {str(e)}")


@router.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    接收 Emby Webhook 事件
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    background_tasks.add_task(notification_service.process_event, payload)
    return Response(status_code=200)


@router.get("/settings")
async def get_settings():
    """获取通知设置"""
    try:
        settings = notification_settings_store.get_settings()
        settings_dict = settings.model_dump()
        
        # 包含有效的 webhook URL
        effective_webhook_urls = []
        if settings.discord_enabled and settings.discord_webhooks:
            for webhook in settings.discord_webhooks:
                if webhook.url:
                    effective_webhook_urls.append(webhook.url)
        
        settings_dict['effective_webhook_urls'] = effective_webhook_urls
        
        return {
            "success": True,
            "data": settings_dict
        }
    except Exception as e:
        logger.error(f"[Notifications] 获取设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取设置失败: {str(e)}")


@router.post("/settings")
async def save_notification_settings(settings: list):
    """保存通知设置（前端格式）"""
    try:
        if not settings or len(settings) == 0:
            raise HTTPException(status_code=400, detail="无效的设置数据")
        
        # 提取第一个设置对象的 conditions 字段，它包含了所有通道配置
        setting = settings[0]
        conditions = setting.get('conditions', {})
        
        # 构建后端需要的设置格式
        backend_settings = {}
        
        # Emby 配置
        emby_config = conditions.get('emby', {})
        if emby_config.get('enabled'):
            backend_settings['emby_connection'] = {
                'url': emby_config.get('server_url', ''),
                'api_key': emby_config.get('api_token', '')
            }
        
        # Telegram 配置
        telegram_config = conditions.get('telegram', {})
        backend_settings['telegram_enabled'] = telegram_config.get('enabled', False)
        if telegram_config.get('bot_token'):
            backend_settings['telegram_bot_token'] = telegram_config.get('bot_token')
        backend_settings['telegram_admins'] = [
            {'user_id': uid, 'name': None}
            for uid in telegram_config.get('admin_users', [])
        ]
        backend_settings['telegram_users'] = [
            {'user_id': uid, 'name': None}
            for uid in telegram_config.get('regular_users', [])
        ]
        
        # Discord 配置
        discord_config = conditions.get('discord', {})
        backend_settings['discord_enabled'] = discord_config.get('enabled', False)
        if discord_config.get('webhook_url'):
            backend_settings['discord_webhooks'] = [{
                'url': discord_config.get('webhook_url'),
                'username': discord_config.get('username', 'Emby Stats')
            }]
        else:
            backend_settings['discord_webhooks'] = []
        
        # WeCom 配置
        wecom_config = conditions.get('wecom', {})
        backend_settings['wecom_enabled'] = wecom_config.get('enabled', False)
        if wecom_config.get('corp_id'):
            backend_settings['wecom_config'] = {
                'corp_id': wecom_config.get('corp_id', ''),
                'corp_secret': wecom_config.get('corp_secret', ''),
                'agent_id': wecom_config.get('agent_id', ''),
                'proxy': wecom_config.get('proxy_url'),
                'to_user': ','.join(wecom_config.get('user_list', []))
            }
        
        # TMDB 配置
        tmdb_config = conditions.get('tmdb', {})
        backend_settings['tmdb_enabled'] = tmdb_config.get('enabled', False)
        if tmdb_config.get('api_key'):
            backend_settings['tmdb_config'] = {
                'api_key': tmdb_config.get('api_key', '')
            }
        
        # 更新设置
        success, error = notification_settings_store.update_settings(backend_settings)
        
        if not success:
            raise HTTPException(status_code=400, detail=error or "更新设置失败")
        
        return {
            "status": "success",
            "message": "设置已保存"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Notifications] 保存设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存设置失败: {str(e)}")


@router.put("/settings")
async def update_settings(request: SettingsUpdateRequest):
    """更新通知设置"""
    try:
        # 获取当前设置
        current_settings = notification_settings_store.get_settings()
        current_dict = current_settings.model_dump()
        
        # 合并更新数据
        update_data = {}
        for field, value in request.model_dump(exclude_none=True).items():
            if value is not None:
                update_data[field] = value
        
        # 合并到当前设置
        merged_data = {**current_dict, **update_data}
        
        # 更新设置
        success, error = notification_settings_store.update_settings(merged_data)
        
        if not success:
            raise HTTPException(status_code=400, detail=error or "更新设置失败")
        
        # 返回更新后的设置
        updated_settings = notification_settings_store.get_settings()
        settings_dict = updated_settings.model_dump()
        
        # 包含有效的 webhook URL
        effective_webhook_urls = []
        if updated_settings.discord_enabled and updated_settings.discord_webhooks:
            for webhook in updated_settings.discord_webhooks:
                if webhook.url:
                    effective_webhook_urls.append(webhook.url)
        
        settings_dict['effective_webhook_urls'] = effective_webhook_urls
        
        return {
            "success": True,
            "data": settings_dict,
            "message": "设置已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Notifications] 更新设置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新设置失败: {str(e)}")


@router.get("/templates")
async def get_templates():
    """获取所有通知模板"""
    try:
        templates = notification_settings_store.get_templates()
        return {
            "success": True,
            "data": templates
        }
    except Exception as e:
        logger.error(f"[Notifications] 获取模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


@router.put("/templates/{template_id}")
async def update_template(template_id: str, request: TemplateRequest):
    """更新指定模板"""
    try:
        # 验证模板ID
        valid_template_ids = ['default', 'playback', 'login', 'mark', 'library']
        if template_id not in valid_template_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的模板ID。可用选项: {', '.join(valid_template_ids)}"
            )
        
        # 验证并清理字符串
        title = request.title.strip()
        text = request.text.strip()
        
        if not title:
            raise HTTPException(status_code=400, detail="模板标题不能为空")
        
        if not text:
            raise HTTPException(status_code=400, detail="模板内容不能为空")
        
        if len(title) > 200:
            raise HTTPException(status_code=400, detail="模板标题长度不能超过200字符")
        
        if len(text) > 2000:
            raise HTTPException(status_code=400, detail="模板内容长度不能超过2000字符")
        
        # 准备更新数据
        template_data = {
            "title": title,
            "text": text,
            "image_template": request.image_template.strip() if request.image_template else None
        }
        
        # 更新模板
        success, error = notification_settings_store.update_template(template_id, template_data)
        
        if not success:
            raise HTTPException(status_code=400, detail=error or "更新模板失败")
        
        # 返回更新后的模板
        templates = notification_settings_store.get_templates()
        
        return {
            "success": True,
            "data": {
                template_id: templates[template_id]
            },
            "message": f"模板 '{template_id}' 已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Notifications] 更新模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")


@router.post("/templates/preview")
async def preview_template(request: TemplatePreviewRequest):
    """预览模板渲染结果"""
    try:
        # 验证模板ID
        valid_template_ids = ['default', 'playback', 'login', 'mark', 'library']
        if request.template_id not in valid_template_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"未知模板ID: {request.template_id}"
            )
        
        # 获取模板
        templates = notification_settings_store.get_templates()
        template_dict = templates.get(request.template_id)
        
        if not template_dict:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 使用 NotificationService 进行渲染
        try:
            rendered = await notification_service.preview_notification(request.template_id, request.content)
            
            return {
                "success": True,
                "data": {
                    "template_id": request.template_id,
                    "original_title": template_dict['title'],
                    "original_text": template_dict['text'],
                    "original_image": template_dict.get('image_template'),
                    "rendered_title": rendered['title'],
                    "rendered_text": rendered['text'],
                    "rendered_image": rendered['image'],
                    "sample_data": request.content
                }
            }
            
        except ValueError as e:
             raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"模板渲染失败: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Notifications] 模板预览失败: {e}")
        raise HTTPException(status_code=500, detail=f"模板预览失败: {str(e)}")
