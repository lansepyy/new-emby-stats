"""
数据库工具模块
提供数据库连接和 SQL 辅助函数
"""
import aiosqlite
from config import settings
from typing import Optional
from config_storage import config_storage


def get_server_config(server_id: Optional[str] = None) -> dict:
    """获取服务器配置
    
    Args:
        server_id: 服务器ID，如果为None则返回默认配置（使用环境变量）
        
    Returns:
        包含数据库路径和其他配置的字典
    """
    if server_id is None:
        # 使用环境变量的默认配置
        return {
            'playback_db': settings.PLAYBACK_DB,
            'users_db': settings.USERS_DB,
            'auth_db': settings.AUTH_DB,
            'emby_url': settings.EMBY_URL,
            'emby_api_key': settings.EMBY_API_KEY
        }
    
    # 从配置存储中获取指定服务器的配置
    servers = config_storage.get("servers", {})
    if server_id not in servers:
        # 如果指定的服务器不存在，回退到默认配置
        return {
            'playback_db': settings.PLAYBACK_DB,
            'users_db': settings.USERS_DB,
            'auth_db': settings.AUTH_DB,
            'emby_url': settings.EMBY_URL,
            'emby_api_key': settings.EMBY_API_KEY
        }
    
    server = servers[server_id]
    # 如果服务器配置中没有指定数据库路径，使用默认路径
    return {
        'playback_db': server.get('playback_db') or settings.PLAYBACK_DB,
        'users_db': server.get('users_db') or settings.USERS_DB,
        'auth_db': server.get('auth_db') or settings.AUTH_DB,
        'emby_url': server.get('emby_url') or settings.EMBY_URL,
        'emby_api_key': server.get('emby_api_key') or settings.EMBY_API_KEY
    }


def get_playback_db(server_id: Optional[str] = None):
    """获取播放记录数据库连接"""
    config = get_server_config(server_id)
    return aiosqlite.connect(config['playback_db'])


def get_users_db(server_id: Optional[str] = None):
    """获取用户数据库连接"""
    config = get_server_config(server_id)
    return aiosqlite.connect(config['users_db'])


def get_auth_db(server_id: Optional[str] = None):
    """获取认证数据库连接"""
    config = get_server_config(server_id)
    return aiosqlite.connect(config['auth_db'])


def get_count_expr() -> str:
    """获取播放次数统计表达式（条件计数，只统计满足时长要求的）"""
    if settings.MIN_PLAY_DURATION > 0:
        return f"SUM(CASE WHEN COALESCE(PlayDuration, 0) >= {settings.MIN_PLAY_DURATION} THEN 1 ELSE 0 END)"
    return "COUNT(*)"


def get_duration_filter() -> str:
    """获取播放时长过滤 SQL 条件（用于最近播放等需要完全过滤的场景）"""
    if settings.MIN_PLAY_DURATION > 0:
        return f" AND COALESCE(PlayDuration, 0) >= {settings.MIN_PLAY_DURATION}"
    return ""


def local_datetime(column: str) -> str:
    """将 UTC 时间列转换为本地时间的 SQL 表达式"""
    offset = settings.TZ_OFFSET
    if offset >= 0:
        return f"datetime({column}, '+{offset} hours')"
    else:
        return f"datetime({column}, '{offset} hours')"


def local_date(column: str) -> str:
    """将 UTC 时间列转换为本地日期的 SQL 表达式"""
    offset = settings.TZ_OFFSET
    if offset >= 0:
        return f"date({column}, '+{offset} hours')"
    else:
        return f"date({column}, '{offset} hours')"


def convert_guid_bytes_to_standard(guid_bytes: bytes) -> str:
    """将 SQLite 中的 GUID 字节转换为标准格式（小写无连字符）
    SQLite 存储的是 .NET GUID 的字节格式，前三部分需要反转字节序
    """
    if len(guid_bytes) != 16:
        return guid_bytes.hex().lower()
    # .NET GUID 格式: 前4字节、接下来2字节、再接下来2字节需要反转，后8字节保持不变
    part1 = guid_bytes[0:4][::-1]  # 反转前4字节
    part2 = guid_bytes[4:6][::-1]  # 反转接下来2字节
    part3 = guid_bytes[6:8][::-1]  # 反转再接下来2字节
    part4 = guid_bytes[8:16]       # 后8字节保持不变
    return (part1 + part2 + part3 + part4).hex().lower()
