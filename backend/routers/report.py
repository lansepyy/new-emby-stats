"""报告推送路由"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from services.report import report_service
from services.report_image import report_image_service
from services.notification import NotificationService
from config_storage import config_storage
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/send")
async def send_report(type: str = Query(..., regex="^(daily|weekly|monthly)$")):
    """手动发送报告
    
    Args:
        type: 报告类型 (daily/weekly/monthly)
    """
    try:
        # 获取报告配置
        report_config = config_storage.get_report_config()
        if not report_config.get("enabled"):
            raise HTTPException(status_code=400, detail="报告推送未启用")
        
        # 生成报告
        if type == "daily":
            report = await report_service.generate_daily_report()
        elif type == "weekly":
            report = await report_service.generate_weekly_report()
        else:  # monthly
            report = await report_service.generate_monthly_report()
        
        # 获取封面图片
        cover_images = await report_service.get_cover_images(report, settings.EMBY_URL)
        
        # 生成图片报告
        report_image = report_image_service.generate_report_image(report, cover_images)
        
        # 格式化为文本（备用）
        report_text = report_service.format_report_text(report)
        
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
        
        # 先上传图片到临时文件，然后发送
        import tempfile
        import os
        
        temp_file = None
        try:
            # 保存图片到临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_file.write(report_image)
            temp_file.close()
            
            # 根据配置的渠道发送
            channels = report_config.get("channels", {"telegram": True})
            sent_count = 0
            
            if channels.get("telegram") and tg_config.get("bot_token"):
                try:
                    # 读取图片并作为文件发送
                    with open(temp_file.name, 'rb') as img_file:
                        notification_service._send_telegram_photo_file_direct(
                            tg_config.get("bot_token"),
                            tg_config.get("admins", []) + tg_config.get("users", []),
                            img_file.read(),
                            report['title']
                        )
                    sent_count += 1
                    logger.info("报告已通过 Telegram 发送")
                except Exception as e:
                    logger.error(f"Telegram 发送失败: {e}")
            
            if channels.get("wecom") and wecom_config.get("corp_id"):
                try:
                    # 企业微信发送文本版本
                    notification_service.send_wecom("观影报告", report_text)
                    sent_count += 1
                    logger.info("报告已通过企业微信发送")
                except Exception as e:
                    logger.error(f"企业微信发送失败: {e}")
            
            if channels.get("discord") and discord_config.get("webhook_url"):
                try:
                    # Discord发送文本版本
                    notification_service.send_discord("观影报告", report_text)
                    sent_count += 1
                    logger.info("报告已通过 Discord 发送")
                except Exception as e:
                    logger.error(f"Discord 发送失败: {e}")
        
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"临时文件删除失败: {e}")
        
        if sent_count == 0:
            raise HTTPException(status_code=400, detail="没有可用的推送渠道或发送失败")
        
        return {
            "success": True,
            "message": f"报告已发送到 {sent_count} 个渠道",
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
