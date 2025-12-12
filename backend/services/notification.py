"""多平台通知服务"""
import logging
from typing import Optional
import requests
from jinja2 import Template
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationService:
    """统一通知服务（支持Telegram/企业微信/Discord）"""
    
    def __init__(self, config: dict):
        self.config = config
        self.telegram_config = config.get("telegram", {})
        self.wecom_config = config.get("wecom", {})
        self.discord_config = config.get("discord", {})
    
    def send_all(self, title: str, message: str, image_url: Optional[str] = None):
        """发送到所有配置的平台"""
        if self.telegram_config.get("token"):
            self.send_telegram(title, message, image_url)
        
        if self.wecom_config.get("corp_id"):
            self.send_wecom(title, message, image_url)
        
        if self.discord_config.get("webhook_url"):
            self.send_discord(title, message, image_url)
    
    def send_telegram(self, title: str, message: str, image_url: Optional[str] = None):
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
                    success = self._send_telegram_photo_url(token, chat_id, image_url, full_message)
                    
                    # 如果URL发送失败，尝试下载后上传文件
                    if not success:
                        logger.info(f"URL发送失败，尝试下载图片后上传")
                        success = self._send_telegram_photo_file(token, chat_id, image_url, full_message)
                    
                    # 如果都失败，发送纯文本
                    if not success:
                        logger.warning(f"图片发送失败，改为发送纯文本")
                        self._send_telegram_text(token, chat_id, full_message)
                else:
                    self._send_telegram_text(token, chat_id, full_message)
            
            except Exception as e:
                logger.error(f"Telegram通知发送失败: {str(e)}")
    
    def _send_telegram_photo_url(self, token: str, chat_id: str, photo_url: str, caption: str) -> bool:
        """通过URL发送Telegram图片"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": "HTML",
            }
            
            resp = requests.post(url, data=data, timeout=15)
            
            if resp.status_code == 200 and resp.json().get("ok"):
                logger.info(f"Telegram图片(URL)发送成功至 {chat_id}")
                return True
            else:
                logger.warning(f"Telegram URL发送失败: {resp.text}")
                return False
        
        except Exception as e:
            logger.warning(f"Telegram URL发送异常: {str(e)}")
            return False
    
    def _send_telegram_photo_file(self, token: str, chat_id: str, photo_url: str, caption: str) -> bool:
        """下载图片后通过文件上传方式发送"""
        temp_file = None
        try:
            # 下载图片
            logger.info(f"开始下载图片: {photo_url}")
            resp = requests.get(photo_url, timeout=30, stream=True)
            
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
            for chunk in resp.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
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
                
                resp = requests.post(url, data=data, files=files, timeout=30)
                
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
    
    def _send_telegram_text(self, token: str, chat_id: str, text: str) -> bool:
        """发送Telegram纯文本消息"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            resp = requests.post(url, data=data, timeout=15)
            
            if resp.status_code == 200 and resp.json().get("ok"):
                logger.info(f"Telegram文本发送成功至 {chat_id}")
                return True
            else:
                logger.error(f"Telegram文本发送失败: {resp.text}")
                return False
        
        except Exception as e:
            logger.error(f"Telegram文本发送异常: {str(e)}")
            return False
    
    def send_wecom(self, title: str, message: str, image_url: Optional[str] = None):
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
            
            token_res = requests.get(token_url, params=params, timeout=10)
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
            
            send_res = requests.post(
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
    
    def send_discord(self, title: str, message: str, image_url: Optional[str] = None):
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
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
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
