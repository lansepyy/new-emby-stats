"""
配置管理模块
集中管理所有环境变量和配置项
"""
import os
import json


class Settings:
    """应用配置"""

    # 数据库路径
    PLAYBACK_DB: str = os.getenv("PLAYBACK_DB", "/data/playback_reporting.db")
    USERS_DB: str = os.getenv("USERS_DB", "/data/users.db")
    AUTH_DB: str = os.getenv("AUTH_DB", "/data/authentication.db")

    # Emby 服务器配置
    EMBY_URL: str = os.getenv("EMBY_URL", "http://localhost:8096")
    EMBY_API_KEY: str = os.getenv("EMBY_API_KEY", "")

    # 播放过滤配置
    # 最小播放时长过滤（秒），低于此时长的记录将被忽略，0 表示不过滤
    MIN_PLAY_DURATION: int = int(os.getenv("MIN_PLAY_DURATION", "0"))

    # 时区偏移（小时），用于 SQLite 查询时间转换，上海时区为 +8
    TZ_OFFSET: int = int(os.getenv("TZ_OFFSET", "8"))

    # 缓存配置
    ITEM_CACHE_MAX_SIZE: int = 500
    ITEM_CACHE_EVICT_COUNT: int = 100

    # ============= Webhook 通知配置 =============
    
    # Telegram配置
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMINS: list = json.loads(os.getenv("TELEGRAM_ADMINS", "[]"))
    TELEGRAM_USERS: list = json.loads(os.getenv("TELEGRAM_USERS", "[]"))
    
    # 企业微信配置
    WECOM_CORP_ID: str = os.getenv("WECOM_CORP_ID", "")
    WECOM_SECRET: str = os.getenv("WECOM_SECRET", "")
    WECOM_AGENT_ID: str = os.getenv("WECOM_AGENT_ID", "")
    WECOM_PROXY_URL: str = os.getenv("WECOM_PROXY_URL", "https://qyapi.weixin.qq.com")
    WECOM_TO_USER: str = os.getenv("WECOM_TO_USER", "@all")
    
    # Discord配置
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    DISCORD_USERNAME: str = os.getenv("DISCORD_USERNAME", "Emby通知")
    DISCORD_AVATAR_URL: str = os.getenv("DISCORD_AVATAR_URL", "")
    
    # TMDB配置
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_IMAGE_BASE_URL: str = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p/original")
    
    # 通知模板配置
    NOTIFICATION_TEMPLATES: dict = {
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


settings = Settings()
