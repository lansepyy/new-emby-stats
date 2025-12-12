"""配置存储管理"""
import json
import os
from typing import Dict, Any
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

CONFIG_FILE = "/data/webhook_config.json"

DEFAULT_CONFIG = {
    "telegram": {
        "bot_token": "",
        "admins": [],
        "users": []
    },
    "wecom": {
        "corp_id": "",
        "secret": "",
        "agent_id": "",
        "proxy_url": "https://qyapi.weixin.qq.com",
        "to_user": "@all"
    },
    "discord": {
        "webhook_url": "",
        "username": "Emby通知",
        "avatar_url": ""
    },
    "tmdb": {
        "api_key": "",
        "image_base_url": "https://image.tmdb.org/t/p/original"
    },
    "report": {
        "enabled": False,
        "daily_enabled": False,
        "weekly_enabled": False,
        "monthly_enabled": False,
        "daily_time": "21:00",
        "weekly_time": "21:00",
        "weekly_day": 0,
        "monthly_time": "21:00",
        "monthly_day": 1,
        "channels": {
            "telegram": True,
            "wecom": False,
            "discord": False
        }
    },
    "servers": {},
    "templates": {
        "default": {
            "title": "{% if action == '新入库' and media_type == '电影' %}🎬 {% elif action == '新入库' and media_type == '剧集' %}📺 {% elif action == '新入库' and media_type == '有声书' %}📚 {% elif action == '新入库' %}🆕 {% elif action == '测试' %}🧪 {% elif action == '开始播放' %}▶️ {% elif action == '停止播放' %}⏹️ {% elif action == '登录成功' %}✅ {% elif action == '登录失败' %}❌ {% elif action == '标记了' %}🏷️ {% endif %}{% if user_name %}【{{ user_name }}】{% endif %}{{ action }}{% if media_type %} {{ media_type }} {% endif %}{{ item_name }}",
            "text": "{% if rating %}⭐ 评分：{{ rating }}/10\n{% endif %}📚 类型：{{ media_type }}\n{% if progress %}🔄 进度：{{ progress }}%\n{% endif %}{% if ip_address %}🌐 IP地址：{{ ip_address }}\n{% endif %}{% if device_name %}📱 设备：{{ client }} {{ device_name }}\n{% endif %}{% if size %}💾 大小：{{ size }}\n{% endif %}{% if tmdb_id %}🎬 TMDB ID：{{ tmdb_id }}\n{% endif %}{% if imdb_id %}🎞️ IMDB ID：{{ imdb_id }}\n{% endif %}🕒 时间：{{ now_time }}\n{% if overview %}\n📝 剧情：{{ overview }}{% endif %}"
        },
        "playback": {
            "title": "{% if action == '开始播放' %}▶️ {{ action }} {{ media_type }}：{{ item_name }}{% if item_year %}（{{ item_year }}）{% endif %}{% endif %}{% if action == '停止播放' %}⏹️ {{ action }} {{ media_type }}：{{ item_name }}{% if item_year %}（{{ item_year }}）{% endif %}{% endif %}{% if action == '暂停播放' %}⏸️ {{ action }} {{ media_type }}：{{ item_name }}{% if item_year %}（{{ item_year }}）{% endif %}{% endif %}",
            "text": "{% if media_type == '电影' %}🎬 类型：电影{% elif media_type == '电视剧' %}📺 类型：电视剧{% else %}🎥 类型：{{ media_type }}{% endif %}\n{% if rating %}🌟 评分：{{ rating }}/10\n{% endif %}🙋 用户：{{ user_name }}\n📱 设备：{{ device_name }}\n🌐 IP：{{ ip_address }}\n{% if progress %}🔄 进度：{{ progress }}%\n{% endif %}🕒 时间：{{ now_time }}\n{% if overview %}📜 剧情：{{ overview }}{% endif %}"
        },
        "library": {
            "title": "{% if media_type == '电影' %}🎬{% elif media_type == '剧集' %}📺{% else %}🆕{% endif %} 新入库 {{ media_type }}：{{ item_name }}",
            "text": "{% if media_type == '电影' %}🎬 类型：电影{% elif media_type == '剧集' %}📺 类型：剧集{% else %}🆕 类型：{{ media_type }}{% endif %}\n{% if rating %}⭐ 评分：{{ rating }}/10\n{% endif %}{% if item_year %}📅 年份：{{ item_year }}\n{% endif %}{% if size %}💾 大小：{{ size }}\n{% endif %}🕒 时间：{{ now_time }}\n{% if overview %}📝 简介：{{ overview }}{% endif %}"
        },
        "login": {
            "title": "{% if action == '登录成功' %}🔑 登录成功 ✅{% elif action == '登录失败' %}🔓 登录失败 ❌{% else %}🚪 用户登录通知{% endif %}",
            "text": "🙋 用户：{{ user_name }}\n💻 平台：{{ client }}\n📱 设备：{{ device_name }}\n🌍 IP地址：{{ ip_address }}\n🕒 登录时间：{{ now_time }}"
        },
        "mark": {
            "title": "🏷️ {{ user_name }} {{ action }} {{ media_type }}：{{ item_name }}",
            "text": "{% if rating %}⭐ 评分：{{ rating }}\n{% endif %}📺 类型：{{ media_type }}\n🕒 时间：{{ now_time }}\n{% if overview %}📝 简介：{{ overview }}{% endif %}"
        }
    }
}


class ConfigStorage:
    """配置文件存储管理"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self._ensure_config_exists()
        self._ensure_default_server()
    
    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_file):
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            # 创建默认配置
            self.save_config(DEFAULT_CONFIG)
            logger.info(f"创建默认配置文件: {self.config_file}")
    
    def _ensure_default_server(self):
        """确保至少有一个默认服务器配置"""
        config = self.load_config()
        servers = config.get("servers", {})
        
        # 如果没有任何服务器，创建默认服务器
        if not servers:
            from config import settings
            default_server_id = str(uuid.uuid4())
            servers[default_server_id] = {
                "name": "默认服务器",
                "emby_url": settings.EMBY_URL,
                "playback_db": settings.PLAYBACK_DB,
                "users_db": settings.USERS_DB,
                "auth_db": settings.AUTH_DB,
                "emby_api_key": settings.EMBY_API_KEY,
                "is_default": True,
                "created_at": datetime.now().isoformat()
            }
            config["servers"] = servers
            self.save_config(config)
            logger.info(f"创建默认服务器配置: {default_server_id}")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("配置加载成功")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            raise
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """获取Telegram配置"""
        config = self.load_config()
        return config.get("telegram", DEFAULT_CONFIG["telegram"])
    
    def get_wecom_config(self) -> Dict[str, Any]:
        """获取企业微信配置"""
        config = self.load_config()
        return config.get("wecom", DEFAULT_CONFIG["wecom"])
    
    def get_discord_config(self) -> Dict[str, Any]:
        """获取Discord配置"""
        config = self.load_config()
        return config.get("discord", DEFAULT_CONFIG["discord"])
    
    def get_tmdb_config(self) -> Dict[str, Any]:
        """获取TMDB配置"""
        config = self.load_config()
        return config.get("tmdb", DEFAULT_CONFIG["tmdb"])
    
    def get_report_config(self) -> Dict[str, Any]:
        """获取报告推送配置"""
        config = self.load_config()
        return config.get("report", DEFAULT_CONFIG["report"])
    
    def get_templates(self) -> Dict[str, Any]:
        """获取通知模板"""
        config = self.load_config()
        return config.get("templates", DEFAULT_CONFIG["templates"])
    
    def get(self, key: str, default=None) -> Any:
        """获取配置项"""
        config = self.load_config()
        return config.get(key, default)
    
    def update_section(self, section: str, data: Dict[str, Any]):
        """更新配置的某个部分"""
        config = self.load_config()
        config[section] = data
        self.save_config(config)


# 全局配置存储实例
config_storage = ConfigStorage()
