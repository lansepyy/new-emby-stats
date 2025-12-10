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


@router.put("/settings")
async def update_settings(request: SettingsUpdateRequest):
    """更新通知设置"""
    try:
        # 获取当前设置
        current_settings = notification_settings_store.get_settings()
        current_dict = current_settings.dict()
        
        # 合并更新数据
        update_data = {}
        for field, value in request.dict(exclude_none=True).items():
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
