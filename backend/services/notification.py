"""多平台通知服务"""
import logging
from typing import Optional
import requests
import httpx
from jinja2 import Template
import tempfile
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationService:
    """统一通知服务（支持Telegram/企业微信/Discord）"""
    
    def __init__(self, config: dict):
        self.config = config
        self.telegram_config = config.get("telegram", {})
        self.wecom_config = config.get("wecom", {})
        self.discord_config = config.get("discord", {})
    
    async def send_all(self, title: str, message: str, image_url: Optional[str] = None):
        """发送到所有配置的平台"""
        if self.telegram_config.get("token"):
            await self.send_telegram(title, message, image_url)
        
        if self.wecom_config.get("corp_id"):
            await self.send_wecom(title, message, image_url)
        
        if self.discord_config.get("webhook_url"):
            await self.send_discord(title, message, image_url)
    
    async def send_telegram(self, title: str, message: str, image_url: Optional[str] = None):
        """发送Telegram通知"""
        token = self.telegram_config.get("token")
        if not token:
            return
        
        admins = self.telegram_config.get("admins", [])
        users = self.telegram_config.get("users", [])
        all_recipients = admins + users
        
        if not all_recipients:
            logger.warning("Telegram未配置接收者")
            return
        
        full_message = f"<b>{title}</b>\n{message}"
        
        for chat_id in all_recipients:
            try:
                if image_url:
                    # 尝试使用URL直接发送
                    success = await self._send_telegram_photo_url(token, chat_id, image_url, full_message)
                    
                    # 如果URL发送失败，尝试下载后上传文件
                    if not success:
                        logger.info(f"URL发送失败，尝试下载图片后上传")
                        success = await self._send_telegram_photo_file(token, chat_id, image_url, full_message)
                    
                    # 如果都失败，发送纯文本
                    if not success:
                        logger.warning(f"图片发送失败，改为发送纯文本")
                        await self._send_telegram_text(token, chat_id, full_message)
                else:
                    await self._send_telegram_text(token, chat_id, full_message)
            
            except Exception as e:
                logger.error(f"Telegram通知发送失败: {str(e)}")
    
    async def _send_telegram_photo_url(self, token: str, chat_id: str, photo_url: str, caption: str) -> bool:
        """通过URL发送Telegram图片"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": "HTML",
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data, timeout=15)
            
            if resp.status_code == 200 and resp.json().get("ok"):
                logger.info(f"Telegram图片(URL)发送成功至 {chat_id}")
                return True
            else:
                logger.warning(f"Telegram URL发送失败: {resp.text}")
                return False
        
        except Exception as e:
            logger.warning(f"Telegram URL发送异常: {str(e)}")
            return False
    
    async def _send_telegram_photo_file(self, token: str, chat_id: str, photo_url: str, caption: str) -> bool:
        """下载图片后通过文件上传方式发送"""
        temp_file = None
        try:
            # 下载图片
            logger.info(f"开始下载图片: {photo_url}")
            async with httpx.AsyncClient() as client:
                resp = await client.get(photo_url, timeout=30)
            
            if resp.status_code != 200:
                logger.warning(f"图片下载失败: HTTP {resp.status_code}")
                return False
            
            # 获取文件扩展名
            content_type = resp.headers.get('Content-Type', '')
            ext = '.jpg'
            if 'png' in content_type:
                ext = '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'webp' in content_type:
                ext = '.webp'
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            # 写入图片数据
            temp_file.write(resp.content)
            temp_file.close()
            
            # 通过文件上传发送
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            with open(temp_file.name, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, data=data, files=files, timeout=30)
                
                if resp.status_code == 200 and resp.json().get("ok"):
                    logger.info(f"Telegram图片(文件)发送成功至 {chat_id}")
                    return True
                else:
                    logger.error(f"Telegram文件上传失败: {resp.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Telegram文件上传异常: {str(e)}")
            return False
        
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                    logger.debug(f"临时文件已删除: {temp_file.name}")
                except Exception as e:
                    logger.warning(f"临时文件删除失败: {str(e)}")
    
    async def _send_telegram_text(self, token: str, chat_id: str, text: str) -> bool:
        """发送Telegram纯文本消息"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=data, timeout=15)
            
            if resp.status_code == 200 and resp.json().get("ok"):
                logger.info(f"Telegram文本发送成功至 {chat_id}")
                return True
            else:
                logger.error(f"Telegram文本发送失败: {resp.text}")
                return False
        
        except Exception as e:
            logger.error(f"Telegram文本发送异常: {str(e)}")
            return False
    
    def _send_telegram_photo_file_direct(self, token: str, chat_ids: list, photo_bytes: bytes, caption: str):
        """直接发送图片字节到多个chat_id"""
        for chat_id in chat_ids:
            try:
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                files = {'photo': ('report.png', photo_bytes, 'image/png')}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                }
                
                resp = requests.post(url, data=data, files=files, timeout=30)
                
                if resp.status_code == 200 and resp.json().get("ok"):
                    logger.info(f"Telegram图片发送成功至 {chat_id}")
                else:
                    logger.error(f"Telegram图片发送失败: {resp.text}")
            
            except Exception as e:
                logger.error(f"Telegram图片发送异常: {str(e)}")
    
    def _send_wecom_photo_bytes(self, photo_bytes: bytes, caption: str):
        """发送企业微信图片（从字节）"""
        required_fields = ["corp_id", "secret", "agent_id"]
        if not all(self.wecom_config.get(field) for field in required_fields):
            logger.warning("企业微信配置不完整，跳过发送")
            return False
        
        try:
            # 获取access_token
            proxy_url = self.wecom_config.get("proxy_url", "https://qyapi.weixin.qq.com")
            token_url = f"{proxy_url}/cgi-bin/gettoken"
            params = {
                "corpid": self.wecom_config["corp_id"],
                "corpsecret": self.wecom_config["secret"]
            }
            
            token_res = requests.get(token_url, params=params, timeout=10)
            token_data = token_res.json()
            
            if token_data.get("errcode") != 0:
                logger.error(f"获取企业微信token失败: {token_data}")
                return False
            
            access_token = token_data["access_token"]
            
            # 上传图片获取media_id
            upload_url = f"{proxy_url}/cgi-bin/media/upload"
            files = {'media': ('report.png', photo_bytes, 'image/png')}
            upload_params = {
                "access_token": access_token,
                "type": "image"
            }
            
            upload_res = requests.post(upload_url, params=upload_params, files=files, timeout=30)
            upload_data = upload_res.json()
            
            if upload_data.get("errcode") != 0 and "media_id" not in upload_data:
                logger.error(f"企业微信图片上传失败: {upload_data}")
                return False
            
            media_id = upload_data["media_id"]
            
            # 发送图片消息
            send_url = f"{proxy_url}/cgi-bin/message/send"
            to_user = self.wecom_config.get("to_user", "@all")
            
            data = {
                "touser": to_user,
                "msgtype": "image",
                "agentid": self.wecom_config["agent_id"],
                "image": {
                    "media_id": media_id
                }
            }
            
            send_res = requests.post(
                send_url,
                params={"access_token": access_token},
                json=data,
                timeout=10
            )
            
            send_data = send_res.json()
            if send_data.get("errcode") == 0:
                logger.info("企业微信图片发送成功")
                
                # 如果有标题，再发送一条文本消息
                if caption:
                    text_data = {
                        "touser": to_user,
                        "msgtype": "text",
                        "agentid": self.wecom_config["agent_id"],
                        "text": {
                            "content": caption
                        }
                    }
                    requests.post(
                        send_url,
                        params={"access_token": access_token},
                        json=text_data,
                        timeout=10
                    )
                
                return True
            else:
                logger.error(f"企业微信图片消息发送失败: {send_data}")
                return False
        
        except Exception as e:
            logger.error(f"企业微信图片发送异常: {str(e)}")
            return False
    
    def _send_discord_photo_bytes(self, photo_bytes: bytes, caption: str):
        """发送Discord图片（从字节）"""
        webhook_url = self.discord_config.get("webhook_url")
        if not webhook_url:
            logger.warning("Discord webhook未配置，跳过发送")
            return False
        
        try:
            files = {'file': ('report.png', photo_bytes, 'image/png')}
            payload = {
                "username": self.discord_config.get("username", "New Emby Stats"),
                "content": caption
            }
            
            # Discord webhook支持multipart/form-data上传文件
            response = requests.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files=files,
                timeout=30
            )
            
            if response.status_code in (200, 204):
                logger.info("Discord图片发送成功")
                return True
            else:
                logger.error(f"Discord图片发送失败: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Discord图片发送异常: {str(e)}")
            return False

    
    async def send_wecom(self, title: str, message: str, image_url: Optional[str] = None):
        """发送企业微信通知"""
        required_fields = ["corp_id", "secret", "agent_id"]
        if not all(self.wecom_config.get(field) for field in required_fields):
            return
        
        try:
            # 获取access_token
            proxy_url = self.wecom_config.get("proxy_url", "https://qyapi.weixin.qq.com")
            token_url = f"{proxy_url}/cgi-bin/gettoken"
            params = {
                "corpid": self.wecom_config["corp_id"],
                "corpsecret": self.wecom_config["secret"]
            }
            
            async with httpx.AsyncClient() as client:
                token_res = await client.get(token_url, params=params, timeout=10)
            token_data = token_res.json()
            
            if token_data.get("errcode") != 0:
                logger.error(f"获取企业微信token失败: {token_data}")
                return
            
            access_token = token_data["access_token"]
            send_url = f"{proxy_url}/cgi-bin/message/send"
            
            to_user = self.wecom_config.get("to_user", "@all")
            
            # 构建消息
            if image_url:
                # 图文消息
                data = {
                    "touser": to_user,
                    "msgtype": "news",
                    "agentid": self.wecom_config["agent_id"],
                    "news": {
                        "articles": [{
                            "title": title,
                            "description": message,
                            "url": "#",
                            "picurl": image_url
                        }]
                    }
                }
            else:
                # 文本卡片
                data = {
                    "touser": to_user,
                    "msgtype": "textcard",
                    "agentid": self.wecom_config["agent_id"],
                    "textcard": {
                        "title": title,
                        "description": message.replace('\n', '<br>'),
                        "url": "#",
                        "btntxt": "详情"
                    }
                }
            
            async with httpx.AsyncClient() as client:
                send_res = await client.post(
                    send_url,
                    params={"access_token": access_token},
                    json=data,
                    timeout=10
                )
            
            if send_res.json().get("errcode") == 0:
                logger.info("企业微信通知发送成功")
            else:
                logger.error(f"企业微信消息发送失败: {send_res.json()}")
        
        except Exception as e:
            logger.error(f"企业微信通知异常: {str(e)}")
    
    async def send_discord(self, title: str, message: str, image_url: Optional[str] = None):
        """发送Discord通知"""
        webhook_url = self.discord_config.get("webhook_url")
        if not webhook_url:
            return
        
        try:
            payload = {
                "username": self.discord_config.get("username", "Emby通知"),
                "content": f"**{title}**\n{message}",
                "avatar_url": self.discord_config.get("avatar_url")
            }
            
            if image_url:
                payload["embeds"] = [{
                    "image": {"url": image_url},
                    "color": 0x00ff00
                }]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("Discord通知发送成功")
            else:
                logger.error(f"Discord通知发送失败: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Discord通知异常: {str(e)}")


class NotificationTemplateService:
    """通知模板渲染服务"""
    
    def __init__(self, templates: dict):
        self.templates = templates
    
    def render(self, template_name: str, context: dict) -> tuple[str, str]:
        """渲染模板，返回(title, message)"""
        template = self.templates.get(template_name, self.templates.get("default"))
        
        if not template:
            return context.get("action", "通知"), str(context)
        
        try:
            title_template = Template(template.get("title", "{{ action }}"))
            message_template = Template(template.get("text", ""))
            
            title = title_template.render(context)
            message = message_template.render(context)
            
            return title, message
        
        except Exception as e:
            logger.error(f"模板渲染失败: {str(e)}")
            return context.get("action", "通知"), str(context)
