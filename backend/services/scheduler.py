"""定时任务调度器"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional
from datetime import datetime
import pytz
import httpx

from services.report import report_service
from services.notification import NotificationService
from services.report_image import ReportImageService
from services.browser_screenshot import browser_screenshot_service, PLAYWRIGHT_AVAILABLE
from config_storage import config_storage

logger = logging.getLogger(__name__)

# 使用中国时区
TIMEZONE = pytz.timezone('Asia/Shanghai')


class ReportScheduler:
    """报告定时任务调度器"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
    
    def start(self):
        """启动调度器"""
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
            self._schedule_tasks()
            self.scheduler.start()
            logger.info("报告调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
            logger.info("报告调度器已停止")
    
    def _schedule_tasks(self):
        """配置定时任务"""
        report_config = config_storage.get_report_config()
        
        if not report_config.get("enabled"):
            logger.info("报告推送未启用，跳过定时任务配置")
            return
        
        # 每日报告
        if report_config.get("daily_enabled"):
            daily_time = report_config.get("daily_time", "21:00")
            hour, minute = daily_time.split(":")
            self.scheduler.add_job(
                self._send_daily_report,
                CronTrigger(hour=int(hour), minute=int(minute), timezone=TIMEZONE),
                id="daily_report",
                replace_existing=True
            )
            logger.info(f"每日报告任务已配置：每天 {daily_time} (Asia/Shanghai)")
        
        # 每周报告
        if report_config.get("weekly_enabled"):
            weekly_time = report_config.get("weekly_time", "21:00")
            weekly_day = report_config.get("weekly_day", 0)  # 0=周日
            hour, minute = weekly_time.split(":")
            self.scheduler.add_job(
                self._send_weekly_report,
                CronTrigger(day_of_week=int(weekly_day), hour=int(hour), minute=int(minute), timezone=TIMEZONE),
                id="weekly_report",
                replace_existing=True
            )
            logger.info(f"每周报告任务已配置：每周{['日','一','二','三','四','五','六'][int(weekly_day)]} {weekly_time} (Asia/Shanghai)")
        
        # 每月报告
        if report_config.get("monthly_enabled"):
            monthly_time = report_config.get("monthly_time", "21:00")
            monthly_day = report_config.get("monthly_day", 1)
            hour, minute = monthly_time.split(":")
            self.scheduler.add_job(
                self._send_monthly_report,
                CronTrigger(day=int(monthly_day), hour=int(hour), minute=int(minute), timezone=TIMEZONE),
                id="monthly_report",
                replace_existing=True
            )
            logger.info(f"每月报告任务已配置：每月{monthly_day}日 {monthly_time} (Asia/Shanghai)")
    
    def reload_tasks(self):
        """重新加载任务配置"""
        if self.scheduler:
            # 移除所有现有任务
            self.scheduler.remove_all_jobs()
            # 重新配置
            self._schedule_tasks()
            logger.info("报告任务配置已重新加载")
    
    async def _send_daily_report(self):
        """发送每日报告"""
        try:
            logger.info("开始生成每日报告...")
            report = await report_service.generate_daily_report()
            await self._send_report(report)
            logger.info("每日报告发送成功")
        except Exception as e:
            logger.error(f"发送每日报告失败: {e}")
    
    async def _send_weekly_report(self):
        """发送每周报告"""
        try:
            logger.info("开始生成每周报告...")
            report = await report_service.generate_weekly_report()
            await self._send_report(report)
            logger.info("每周报告发送成功")
        except Exception as e:
            logger.error(f"发送每周报告失败: {e}")
    
    async def _send_monthly_report(self):
        """发送每月报告"""
        try:
            logger.info("开始生成每月报告...")
            report = await report_service.generate_monthly_report()
            await self._send_report(report)
            logger.info("每月报告发送成功")
        except Exception as e:
            logger.error(f"发送每月报告失败: {e}")
    
    async def _send_report(self, report: dict):
        """发送报告到配置的渠道（图片版本）"""
        report_config = config_storage.get_report_config()
        
        # 获取通知配置
        tg_config = config_storage.get_telegram_config()
        wecom_config = config_storage.get_wecom_config()
        discord_config = config_storage.get_discord_config()
        
        channels = report_config.get("channels", {"telegram": True})
        report_title = report.get("title", "观影报告")
        
        # 生成报告图片
        logger.info("开始生成报告图片...")
        image_bytes = None
        
        try:
            # 优先尝试使用浏览器截图（和手动发送一样的高质量）
            if PLAYWRIGHT_AVAILABLE:
                logger.info("使用Playwright浏览器截图生成报告...")
                image_bytes = await browser_screenshot_service.generate_report_screenshot(report)
                
                if image_bytes:
                    logger.info(f"浏览器截图生成成功，大小: {len(image_bytes)} 字节")
                else:
                    logger.warning("浏览器截图生成失败，尝试使用PIL生成")
            
            # 如果浏览器截图失败或不可用，回退到PIL生成
            if not image_bytes:
                logger.info("使用PIL生成报告图片（实时获取封面）...")
                
                # 生成图片（封面将在绘制时实时获取）
                image_service = ReportImageService()
                image_bytes = image_service.generate_report_image(report)
                logger.info(f"PIL图片生成成功，大小: {len(image_bytes)} 字节")
            
        except Exception as e:
            logger.error(f"生成报告图片失败: {e}，将发送文本版本")
            # 如果图片生成失败，回退到文本版本
            await self._send_text_report(report, tg_config, wecom_config, discord_config, channels)
            return
        
        # 发送图片到各个渠道
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
        sent_count = 0
        
        # Telegram
        if channels.get("telegram") and tg_config.get("bot_token"):
            try:
                token = tg_config.get("bot_token")
                recipients = tg_config.get("admins", []) + tg_config.get("users", [])
                
                for chat_id in recipients:
                    success = await notification_service._send_telegram_photo_bytes(
                        token, chat_id, image_bytes, report_title
                    )
                    if success:
                        sent_count += 1
                        logger.info(f"报告图片已通过 Telegram 发送至 {chat_id}")
            except Exception as e:
                logger.error(f"Telegram 发送失败: {e}")
        
        # 企业微信
        if channels.get("wecom") and wecom_config.get("corp_id"):
            try:
                if notification_service._send_wecom_photo_bytes(image_bytes, report_title):
                    sent_count += 1
                    logger.info("报告图片已通过企业微信发送")
            except Exception as e:
                logger.error(f"企业微信发送失败: {e}")
        
        # Discord
        if channels.get("discord") and discord_config.get("webhook_url"):
            try:
                if notification_service._send_discord_photo_bytes(image_bytes, report_title):
                    sent_count += 1
                    logger.info("报告图片已通过 Discord 发送")
            except Exception as e:
                logger.error(f"Discord 发送失败: {e}")
        
        if sent_count == 0:
            logger.warning("没有成功发送到任何渠道")
    
    async def _send_text_report(self, report: dict, tg_config: dict, wecom_config: dict, discord_config: dict, channels: dict):
        """发送文本版本的报告（备用方案）"""
        report_text = report_service.format_report_text(report)
        report_title = report.get("title", "观影报告")
        
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
        
        if channels.get("telegram") and tg_config.get("bot_token"):
            try:
                await notification_service.send_telegram(report_title, report_text)
                logger.info("报告文本已通过 Telegram 发送")
            except Exception as e:
                logger.error(f"Telegram 发送失败: {e}")
        
        if channels.get("wecom") and wecom_config.get("corp_id"):
            try:
                await notification_service.send_wecom(report_title, report_text)
                logger.info("报告文本已通过企业微信发送")
            except Exception as e:
                logger.error(f"企业微信发送失败: {e}")
        
        if channels.get("discord") and discord_config.get("webhook_url"):
            try:
                await notification_service.send_discord(report_title, report_text)
                logger.info("报告文本已通过 Discord 发送")
            except Exception as e:
                logger.error(f"Discord 发送失败: {e}")


# 全局调度器实例
report_scheduler = ReportScheduler()
