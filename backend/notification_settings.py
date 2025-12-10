"""
通知设置模块
集中管理通知配置，包括 Telegram、Discord、WeCom 等通知渠道设置
"""
import os
import json
import threading
from typing import Optional, List, Dict, Callable
from pydantic import BaseModel, Field, field_validator
import logging

logger = logging.getLogger(__name__)

# 配置文件路径（默认保存到 /config 目录，该目录可写）
NOTIFICATION_SETTINGS_FILE = os.getenv("NOTIFICATION_SETTINGS_FILE", "/config/notification_settings.json")


class EmbyConnection(BaseModel):
    """Emby 连接配置"""
    url: str = Field("", description="Emby 服务器地址")
    api_key: Optional[str] = Field(None, description="Emby API 密钥")


class TelegramAdmin(BaseModel):
    """Telegram 管理员配置"""
    user_id: str = Field(..., description="Telegram 用户ID")
    name: Optional[str] = Field(None, description="用户名称")


class TelegramUser(BaseModel):
    """Telegram 用户配置"""
    user_id: str = Field(..., description="Telegram 用户ID")
    name: Optional[str] = Field(None, description="用户名称")
    is_admin: bool = Field(False, description="是否为管理员")


class DiscordWebhook(BaseModel):
    """Discord Webhook 配置"""
    url: str = Field("", description="Discord Webhook URL")
    username: Optional[str] = Field("Emby Stats", description="机器人用户名")


class WeComConfig(BaseModel):
    """WeCom 企业微信配置"""
    corp_id: str = Field("", description="企业ID")
    corp_secret: str = Field("", description="应用密钥")
    agent_id: str = Field("", description="应用ID")
    proxy: Optional[str] = Field(None, description="代理地址")
    to_user: Optional[str] = Field(None, description="接收者用户ID")


class TMDBConfig(BaseModel):
    """TMDB 配置"""
    api_key: str = Field("", description="TMDB API 密钥")


class NotificationTemplate(BaseModel):
    """通知模板配置"""
    title: str = Field(..., description="模板标题", max_length=200)
    text: str = Field(..., description="模板内容", max_length=2000)
    image_template: Optional[str] = Field(None, description="图片模板 URL")
    
    @field_validator('title', 'text')
    @classmethod
    def trim_strings(cls, v):
        """去除首尾空格"""
        if isinstance(v, str):
            return v.strip()
        return v


class NotificationTemplates(BaseModel):
    """通知模板集合"""
    default: NotificationTemplate = Field(default_factory=lambda: NotificationTemplate(
        title="Emby Stats 通知",
        text="这是一条来自 Emby Stats 的通知",
        image_template=None
    ))
    playback: NotificationTemplate = Field(default_factory=lambda: NotificationTemplate(
        title="播放开始通知",
        text="用户 {{ user_name }} 开始播放 {{ item_name }}",
        image_template="{{ item_image }}"
    ))
    login: NotificationTemplate = Field(default_factory=lambda: NotificationTemplate(
        title="登录通知",
        text="用户 {{ user_name }} 登录了系统",
        image_template=None
    ))
    mark: NotificationTemplate = Field(default_factory=lambda: NotificationTemplate(
        title="标记完成通知",
        text="{{ user_name }} 完成了对 {{ item_name }} 的标记",
        image_template="{{ item_image }}"
    ))
    library: NotificationTemplate = Field(default_factory=lambda: NotificationTemplate(
        title="媒体库更新通知",
        text="媒体库已更新，新增 {{ item_count }} 个项目",
        image_template=None
    ))


class NotificationSettings(BaseModel):
    """通知设置配置"""
    # 基础配置
    enabled: bool = Field(False, description="通知功能总开关")
    debug: bool = Field(False, description="调试模式")
    
    # Emby 连接
    emby_connection: EmbyConnection = Field(default_factory=EmbyConnection)
    
    # Telegram 配置
    telegram_enabled: bool = Field(False, description="Telegram 通知开关")
    telegram_bot_token: Optional[str] = Field(None, description="Telegram Bot Token")
    telegram_admins: List[TelegramAdmin] = Field(default_factory=list, description="Telegram 管理员列表")
    telegram_users: List[TelegramUser] = Field(default_factory=list, description="Telegram 用户列表")
    
    # Discord 配置
    discord_enabled: bool = Field(False, description="Discord 通知开关")
    discord_webhooks: List[DiscordWebhook] = Field(default_factory=list, description="Discord Webhook 列表")
    
    # WeCom 配置
    wecom_enabled: bool = Field(False, description="WeCom 通知开关")
    wecom_config: WeComConfig = Field(default_factory=WeComConfig)
    
    # TMDB 配置
    tmdb_enabled: bool = Field(False, description="TMDB 开关")
    tmdb_config: TMDBConfig = Field(default_factory=TMDBConfig)
    
    # 模板配置
    templates: NotificationTemplates = Field(default_factory=NotificationTemplates)
    
    @field_validator('telegram_bot_token')
    @classmethod
    def validate_optional_strings(cls, v):
        """确保字符串字段不为空"""
        if isinstance(v, str) and not v.strip():
            return None
        return v
    
    @field_validator('discord_webhooks')
    @classmethod
    def validate_discord_webhooks(cls, v):
        """验证 Discord Webhook URL"""
        if v:
            for webhook in v:
                if webhook.url and not webhook.url.startswith('https://discord'):
                    raise ValueError("Discord Webhook URL 格式不正确")
        return v


# 默认设置
DEFAULT_SETTINGS = {
    "enabled": False,
    "debug": False,
    "emby_connection": {
        "url": "http://localhost:8096",
        "api_key": None
    },
    "telegram_enabled": False,
    "telegram_bot_token": None,
    "telegram_admins": [],
    "telegram_users": [],
    "discord_enabled": False,
    "discord_webhooks": [],
    "wecom_enabled": False,
    "wecom_config": {
        "corp_id": "",
        "corp_secret": "",
        "agent_id": "",
        "proxy": None,
        "to_user": None
    },
    "tmdb_enabled": False,
    "tmdb_config": {
        "api_key": ""
    },
    "templates": {
        "default": {
            "title": "Emby Stats 通知",
            "text": "这是一条来自 Emby Stats 的通知",
            "image_template": None
        },
        "playback": {
            "title": "播放开始通知",
            "text": "用户 {{ user_name }} 开始播放 {{ item_name }}",
            "image_template": "{{ item_image }}"
        },
        "login": {
            "title": "登录通知",
            "text": "用户 {{ user_name }} 登录了系统",
            "image_template": None
        },
        "mark": {
            "title": "标记完成通知",
            "text": "{{ user_name }} 完成了对 {{ item_name }} 的标记",
            "image_template": "{{ item_image }}"
        },
        "library": {
            "title": "媒体库更新通知",
            "text": "媒体库已更新，新增 {{ item_count }} 个项目",
            "image_template": None
        }
    }
}


class NotificationSettingsStore:
    """通知设置存储服务"""
    
    def __init__(self):
        self._settings: Optional[NotificationSettings] = None
        self._lock = threading.RLock()
        self._change_callbacks: List[Callable] = []
        self._loaded = False
    
    def _load_settings(self) -> NotificationSettings:
        """从文件加载设置"""
        if self._loaded:
            return self._settings
        
        try:
            if os.path.exists(NOTIFICATION_SETTINGS_FILE):
                with open(NOTIFICATION_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 使用当前 Emby 配置作为默认的 Emby 连接
                from config import settings
                if 'emby_connection' not in data or not data['emby_connection'].get('url'):
                    data['emby_connection'] = {
                        'url': settings.EMBY_URL,
                        'api_key': settings.EMBY_API_KEY or None
                    }
                
                self._settings = NotificationSettings(**data)
                logger.info(f"[NotificationSettings] 已加载设置: {NOTIFICATION_SETTINGS_FILE}")
            else:
                logger.info(f"[NotificationSettings] 配置文件不存在: {NOTIFICATION_SETTINGS_FILE}, 使用默认设置")
                self._settings = self._create_default_settings()
                
            self._loaded = True
            return self._settings
            
        except json.JSONDecodeError as e:
            logger.error(f"[NotificationSettings] 配置文件解析失败: {e}")
            self._settings = self._create_default_settings()
            self._loaded = True
            return self._settings
        except Exception as e:
            logger.error(f"[NotificationSettings] 加载设置失败: {e}")
            self._settings = self._create_default_settings()
            self._loaded = True
            return self._settings
    
    def _create_default_settings(self) -> NotificationSettings:
        """创建默认设置"""
        from config import settings
        default_data = DEFAULT_SETTINGS.copy()
        
        # 使用当前配置的 Emby 连接
        default_data['emby_connection'] = {
            'url': settings.EMBY_URL,
            'api_key': settings.EMBY_API_KEY or None
        }
        
        return NotificationSettings(**default_data)
    
    def reload(self) -> None:
        """重新加载设置"""
        with self._lock:
            self._loaded = False
            self._load_settings()
            logger.info("[NotificationSettings] 设置已重新加载")
    
    def get_settings(self) -> NotificationSettings:
        """获取当前设置"""
        with self._lock:
            return self._load_settings()
    
    def update_settings(self, settings_data: dict) -> tuple[bool, Optional[str]]:
        """更新设置"""
        with self._lock:
            try:
                old_settings = self._settings
                
                # 合并现有设置和新数据
                if self._settings:
                    current_data = self._settings.model_dump(exclude_none=False)
                else:
                    current_data = self._create_default_settings().model_dump()
                
                # 深度合并设置数据
                merged_data = self._deep_merge(current_data, settings_data)
                
                new_settings = NotificationSettings(**merged_data)
                
                # 保存到文件
                os.makedirs(os.path.dirname(NOTIFICATION_SETTINGS_FILE), exist_ok=True)
                
                # 转换为字典并保存
                settings_dict = new_settings.model_dump(exclude_none=False)
                with open(NOTIFICATION_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(settings_dict, f, ensure_ascii=False, indent=2)
                
                # 更新内存中的设置
                self._settings = new_settings
                self._loaded = True
                
                logger.info("[NotificationSettings] 设置已保存")
                
                # 触发变更回调
                self._notify_change(old_settings, new_settings)
                
                return True, None
                
            except ValueError as e:
                error_msg = f"设置验证失败: {str(e)}"
                logger.error(f"[NotificationSettings] {error_msg}")
                return False, error_msg
            except Exception as e:
                error_msg = f"保存设置失败: {str(e)}"
                logger.error(f"[NotificationSettings] {error_msg}")
                return False, error_msg
    
    def _deep_merge(self, base: dict, update: dict) -> dict:
        """深度合并字典"""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_templates(self) -> Dict[str, NotificationTemplate]:
        """获取所有模板"""
        settings = self.get_settings()
        return settings.templates.model_dump()
    
    def update_template(self, template_id: str, template_data: dict) -> tuple[bool, Optional[str]]:
        """更新指定模板"""
        if template_id not in ['default', 'playback', 'login', 'mark', 'library']:
            return False, f"未知模板ID: {template_id}"
        
        try:
            with self._lock:
                settings = self.get_settings()
                current_templates = settings.templates.model_dump()
                
                # 验证并创建新模板
                new_template = NotificationTemplate(**template_data)
                current_templates[template_id] = new_template
                
                # 更新设置
                new_settings_data = settings.model_dump()
                new_settings_data['templates'] = current_templates
                
                success, error = self.update_settings(new_settings_data)
                return success, error
                
        except ValueError as e:
            return False, f"模板验证失败: {str(e)}"
        except Exception as e:
            return False, f"更新模板失败: {str(e)}"
    
    def register_change_callback(self, callback: Callable[[NotificationSettings], None]) -> None:
        """注册设置变更回调"""
        self._change_callbacks.append(callback)
    
    def _notify_change(self, old_settings: NotificationSettings, new_settings: NotificationSettings) -> None:
        """通知所有回调"""
        for callback in self._change_callbacks:
            try:
                callback(new_settings)
            except Exception as e:
                logger.error(f"[NotificationSettings] 回调执行失败: {e}")


# 单例实例
notification_settings_store = NotificationSettingsStore()