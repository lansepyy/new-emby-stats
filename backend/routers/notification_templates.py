"""
通知模板管理路由
提供通知模板的CRUD操作和企业微信通知功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
import json

from services.notification_templates import notification_template_service
from services.wecom_notification import wecom_notification_service


router = APIRouter(prefix="/api/notification-templates", tags=["notification-templates"])


@router.get("/")
async def get_templates():
    """获取所有通知模板"""
    try:
        templates = await notification_template_service.get_all_templates()
        return {
            "status": "ok",
            "data": [template.to_dict() for template in templates]
        }
    except Exception as e:
        return {"status": "error", "message": f"获取模板失败: {str(e)}"}


@router.post("/")
async def create_template(data: Dict[str, Any]):
    """创建通知模板"""
    try:
        name = data.get("name", "").strip()
        channel = data.get("channel", "wecom").strip()
        template_content = data.get("template_content", "").strip()
        variables = data.get("variables", [])
        
        if not name:
            raise HTTPException(status_code=400, detail="模板名称不能为空")
        
        if not template_content:
            raise HTTPException(status_code=400, detail="模板内容不能为空")
        
        template = await notification_template_service.create_template(
            name=name,
            channel=channel,
            template_content=template_content,
            variables=variables
        )
        
        return {
            "status": "ok",
            "data": template.to_dict()
        }
    except Exception as e:
        return {"status": "error", "message": f"创建模板失败: {str(e)}"}


@router.put("/{template_id}")
async def update_template(template_id: str, data: Dict[str, Any]):
    """更新通知模板"""
    try:
        name = data.get("name", "").strip()
        template_content = data.get("template_content", "").strip()
        variables = data.get("variables", [])
        
        if not name:
            raise HTTPException(status_code=400, detail="模板名称不能为空")
        
        if not template_content:
            raise HTTPException(status_code=400, detail="模板内容不能为空")
        
        success = await notification_template_service.update_template(
            template_id=template_id,
            name=name,
            template_content=template_content,
            variables=variables
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return {"status": "ok", "message": "模板更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"更新模板失败: {str(e)}"}


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """删除通知模板"""
    try:
        success = await notification_template_service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return {"status": "ok", "message": "模板删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"删除模板失败: {str(e)}"}


@router.post("/{template_id}/render")
async def render_template(template_id: str, context: Dict[str, Any]):
    """渲染通知模板"""
    try:
        rendered_content = await notification_template_service.render_template(template_id, context)
        return {
            "status": "ok",
            "data": {
                "template_id": template_id,
                "rendered_content": rendered_content
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"模板渲染失败: {str(e)}"}


@router.post("/create-defaults")
async def create_default_templates():
    """创建默认模板"""
    try:
        await notification_template_service.create_default_templates()
        return {"status": "ok", "message": "默认模板创建成功"}
    except Exception as e:
        return {"status": "error", "message": f"创建默认模板失败: {str(e)}"}


# 企业微信配置管理路由
router_wecom = APIRouter(prefix="/api/wecom", tags=["wecom"])


@router_wecom.get("/configs")
async def get_wecom_configs():
    """获取所有企业微信配置"""
    try:
        configs = await wecom_notification_service.get_all_configs()
        return {
            "status": "ok",
            "data": [config.to_dict() for config in configs]
        }
    except Exception as e:
        return {"status": "error", "message": f"获取配置失败: {str(e)}"}


@router_wecom.post("/configs")
async def create_wecom_config(data: Dict[str, Any]):
    """创建企业微信配置"""
    try:
        name = data.get("name", "").strip()
        webhook_url = data.get("webhook_url", "").strip()
        enabled = data.get("enabled", True)
        
        if not name:
            raise HTTPException(status_code=400, detail="配置名称不能为空")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL不能为空")
        
        config = await wecom_notification_service.create_config(
            name=name,
            webhook_url=webhook_url,
            enabled=enabled
        )
        
        return {
            "status": "ok",
            "data": config.to_dict()
        }
    except Exception as e:
        return {"status": "error", "message": f"创建配置失败: {str(e)}"}


@router_wecom.put("/configs/{config_id}")
async def update_wecom_config(config_id: str, data: Dict[str, Any]):
    """更新企业微信配置"""
    try:
        name = data.get("name", "").strip()
        webhook_url = data.get("webhook_url", "").strip()
        enabled = data.get("enabled", True)
        
        if not name:
            raise HTTPException(status_code=400, detail="配置名称不能为空")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL不能为空")
        
        success = await wecom_notification_service.update_config(
            config_id=config_id,
            name=name,
            webhook_url=webhook_url,
            enabled=enabled
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        return {"status": "ok", "message": "配置更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"更新配置失败: {str(e)}"}


@router_wecom.delete("/configs/{config_id}")
async def delete_wecom_config(config_id: str):
    """删除企业微信配置"""
    try:
        success = await wecom_notification_service.delete_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        return {"status": "ok", "message": "配置删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"删除配置失败: {str(e)}"}


@router_wecom.post("/test")
async def test_wecom_connection(data: Dict[str, Any]):
    """测试企业微信连接"""
    try:
        webhook_url = data.get("webhook_url", "").strip()
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="Webhook URL不能为空")
        
        result = await wecom_notification_service.test_connection(webhook_url)
        return {
            "status": "ok" if result["success"] else "error",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"连接测试失败: {str(e)}"}


@router_wecom.post("/send")
async def send_wecom_notification(data: Dict[str, Any]):
    """发送企业微信通知"""
    try:
        config_id = data.get("config_id")
        content = data.get("content", "").strip()
        template_id = data.get("template_id")
        context = data.get("context", {})
        
        if not config_id:
            raise HTTPException(status_code=400, detail="配置ID不能为空")
        
        if not content:
            raise HTTPException(status_code=400, detail="消息内容不能为空")
        
        # 如果提供了模板ID和上下文，先渲染模板
        if template_id and context:
            content = await notification_template_service.render_template(template_id, context)
        
        success = await wecom_notification_service.send_message(config_id, content, template_id)
        
        return {
            "status": "ok" if success else "error",
            "message": "消息发送成功" if success else "消息发送失败"
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": f"发送通知失败: {str(e)}"}


@router_wecom.get("/logs")
async def get_wecom_logs(limit: int = Query(50, ge=1, le=200)):
    """获取企业微信通知日志"""
    try:
        logs = await wecom_notification_service.get_logs(limit)
        return {
            "status": "ok",
            "data": logs
        }
    except Exception as e:
        return {"status": "error", "message": f"获取日志失败: {str(e)}"}


@router_wecom.get("/statistics")
async def get_wecom_statistics():
    """获取企业微信通知统计"""
    try:
        stats = await wecom_notification_service.get_statistics()
        return {
            "status": "ok",
            "data": stats
        }
    except Exception as e:
        return {"status": "error", "message": f"获取统计失败: {str(e)}"}


# 将企业微信路由添加到主路由中
router.include_router(router_wecom)