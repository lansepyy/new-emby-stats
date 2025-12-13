"""报告推送路由"""
from fastapi import APIRouter, Query, HTTPException, File, UploadFile, Form
from typing import Optional
import logging

from services.report import report_service
from services.notification import NotificationService
from config_storage import config_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/generate")
async def generate_report(type: str = Query(..., regex="^(daily|weekly|monthly)$")):
    """生成报告数据（供前端使用）
    
    Args:
        type: 报告类型 (daily/weekly/monthly)
    """
    try:
        # 生成报告
        if type == "daily":
            report = await report_service.generate_daily_report()
        elif type == "weekly":
            report = await report_service.generate_weekly_report()
        else:  # monthly
            report = await report_service.generate_monthly_report()
        
        return report
        
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-image")
async def send_report_image(
    image: UploadFile = File(...),
    type: str = Form(...)
):
    """接收前端生成的报告图片并发送
    
    Args:
        image: 报告图片文件
        type: 报告类型
    """
    try:
        # 获取报告配置
        report_config = config_storage.get_report_config()
        if not report_config.get("enabled"):
            raise HTTPException(status_code=400, detail="报告推送未启用")
        
        # 读取图片数据
        image_bytes = await image.read()
        
        # 获取通知配置
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
        
        # 初始化通知服务
        notification_service = NotificationService(notification_config)
        
        # 根据配置的渠道发送
        channels = report_config.get("channels", {"telegram": True})
        sent_count = 0
        
        title_map = {
            "daily": "📊 每日观影报告",
            "weekly": "📊 本周观影报告",
            "monthly": "📊 本月观影报告"
        }
        caption = title_map.get(type, "📊 观影报告")
        
        if channels.get("telegram") and tg_config.get("bot_token"):
            try:
                notification_service._send_telegram_photo_file_direct(
                    tg_config.get("bot_token"),
                    tg_config.get("admins", []) + tg_config.get("users", []),
                    image_bytes,
                    caption
                )
                sent_count += 1
                logger.info("报告图片已通过 Telegram 发送")
            except Exception as e:
                logger.error(f"Telegram 发送失败: {e}")
        
        if channels.get("wecom") and wecom_config.get("corp_id"):
            try:
                if notification_service._send_wecom_photo_bytes(image_bytes, caption):
                    sent_count += 1
                    logger.info("报告图片已通过企业微信发送")
            except Exception as e:
                logger.error(f"企业微信发送失败: {e}")
        
        if channels.get("discord") and discord_config.get("webhook_url"):
            try:
                if notification_service._send_discord_photo_bytes(image_bytes, caption):
                    sent_count += 1
                    logger.info("报告图片已通过 Discord 发送")
            except Exception as e:
                logger.error(f"Discord 发送失败: {e}")

        
        if sent_count == 0:
            raise HTTPException(status_code=400, detail="没有可用的推送渠道或发送失败")
        
        return {
            "success": True,
            "message": f"报告已发送到 {sent_count} 个渠道"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_report(type: str = Query(..., regex="^(daily|weekly|monthly)$")):
    """手动发送报告（文本版本，已废弃，保留兼容性）
    
    Args:
        type: 报告类型 (daily/weekly/monthly)
    """
    return {
        "success": False,
        "message": "请使用前端生成的图片报告功能"
    }

