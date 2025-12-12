"""Webhook事件处理服务"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class WebhookService:
    """处理Emby Webhook事件"""
    
    def __init__(self):
        self.event_actions = {
            "playback.start": "开始播放",
            "playback.stop": "停止播放",
            "playback.pause": "暂停播放",
            "playback.unpause": "继续播放",
            "library.new": "新入库",
            "library.deleted": "删除内容",
            "item.markunplayed": "标记未播放",
            "item.markplayed": "标记已播放",
            "item.rate": "评分",
            "user.rating.update": "评分",
            "item.rating.update": "评分",
            "user.favorite.update": "收藏",
            "item.favorite.update": "收藏",
            "user.authenticated": "登录成功",
            "user.authenticationfailed": "登录失败",
            "system.updateavailable": "系统更新可用",
            "system.serverrestartrequired": "需要重启服务器",
        }
    
    def get_event_action(self, event_type: str) -> str:
        """获取事件动作描述"""
        return self.event_actions.get(event_type, event_type)
    
    def get_device_info(self, response: Dict[str, Any]) -> Dict[str, str]:
        """提取设备信息和IP地址"""
        logger.debug("完整响应数据: %s", json.dumps(response, indent=2, ensure_ascii=False))
        
        # 设备名称 - 添加更多可能的位置
        device_name = (
            response.get("DeviceName") 
            or response.get("Client")
            or response.get("Session", {}).get("DeviceName")
            or response.get("Device", {}).get("DeviceName")
            or response.get("Session", {}).get("Client")
            or response.get("AppName")
            or response.get("ClientName")
            or "未知设备"
        )
        
        # IP地址提取 - 添加更多可能的位置
        ip_address = ""
        ip_sources = [
            "RemoteEndPoint",
            "Session.RemoteEndPoint",
            "PlaybackInfo.RemoteEndPoint",
            "Device.RemoteEndPoint",
            "IpAddress",
            "Session.IpAddress",
        ]
        
        for source in ip_sources:
            try:
                keys = source.split(".")
                value = response
                for key in keys:
                    value = value.get(key, {})
                
                if value and isinstance(value, str):
                    ip = value.split(":")[0] if ":" in value else value
                    if ip and ip != "Unknown":
                        ip_address = ip
                        logger.info(f"从 {source} 提取到IP: {ip_address}")
                        break
            except Exception as e:
                logger.debug(f"从 {source} 提取IP失败: {e}")
                continue
        
        logger.info(f"设备信息: device={device_name}, ip={ip_address}")
        
        return {
            "device_name": device_name,
            "ip_address": ip_address,
        }
    
    def format_progress(self, position_ticks: int, runtime_ticks: int) -> int:
        """计算播放进度百分比"""
        if runtime_ticks > 0:
            return int((position_ticks / runtime_ticks) * 100)
        return 0
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"
    
    def build_event_context(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """构建事件上下文数据"""
        event = response.get("Event")
        if not event:
            logger.error("缺少事件类型")
            return None
        
        # 记录完整的webhook数据用于调试
        logger.info(f"处理事件 {event}，完整数据: {json.dumps(response, indent=2, ensure_ascii=False)}")
        
        user = response.get("User", {})
        user_name = user.get("Name", "未知用户")
        
        # 对于登录失败，用户名可能在不同位置
        if event == "user.authenticationfailed":
            # 尝试从不同位置获取用户名
            user_name = (
                user.get("Name") 
                or response.get("Username")
                or response.get("UserName")
                or response.get("User", {}).get("Name")
                or "未知用户"
            )
            logger.info(f"登录失败事件，提取用户名: {user_name}")
        
        device_info = self.get_device_info(response)
        
        # 北京时间
        beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
        time_str = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 基础上下文
        context = {
            "event": event,
            "action": self.get_event_action(event),
            "user_name": user_name,
            "now_time": time_str,
            "ip_address": device_info.get("ip_address", ""),
            "client": device_info.get("device_name", "未知设备"),
            "device_name": device_info.get("device_name", "未知设备"),
        }
        
        # 播放事件
        playback_events = ("playback.start", "playback.stop", "playback.pause", "playback.unpause")
        if event in playback_events:
            item = response.get("Item", {})
            if not item:
                return None
            
            media_type = "电影" if item.get("Type") == "Movie" else "剧集"
            media_name = item.get("Name", "未知媒体")
            
            if item.get("Type") == "Episode":
                series_name = item.get("SeriesName", "未知剧集")
                season_num = item.get("ParentIndexNumber", 0)
                episode_num = item.get("IndexNumber", 0)
                media_name = f"{series_name} S{season_num}E{episode_num} - {media_name}"
            
            playback_info = response.get("PlaybackInfo", {})
            position_ticks = playback_info.get("PositionTicks", 0)
            runtime_ticks = item.get("RunTimeTicks", 0)
            progress = self.format_progress(position_ticks, runtime_ticks)
            
            context.update({
                "media_type": media_type,
                "item_name": media_name,
                "item_year": item.get("ProductionYear"),
                "overview": item.get("Overview", ""),
                "rating": item.get("CommunityRating"),
                "tmdb_id": item.get("ProviderIds", {}).get("Tmdb"),
                "imdb_id": item.get("ProviderIds", {}).get("Imdb"),
                "progress": progress,
                "item_id": item.get("Id"),
                "item_type": item.get("Type"),
            })
        
        # 入库事件
        elif event == "library.new":
            item = response.get("Item", {})
            if not item:
                return None
            
            if item.get("Type") == "Movie":
                media_type = "电影"
            elif item.get("Type") == "Episode":
                media_type = "剧集"
            elif item.get("Type") == "Audio":
                media_type = "有声书"
            else:
                media_type = item.get("Type", "媒体")
            
            media_name = item.get("Name", "未知媒体")
            if media_type == "剧集":
                series_name = item.get("SeriesName", "未知剧集")
                season_num = item.get("ParentIndexNumber", 0)
                episode_num = item.get("IndexNumber", 0)
                media_name = f"{series_name} S{season_num}E{episode_num} - {media_name}"
            
            context.update({
                "media_type": media_type,
                "item_name": media_name,
                "item_year": item.get("ProductionYear"),
                "overview": item.get("Overview", ""),
                "rating": item.get("CommunityRating"),
                "tmdb_id": item.get("ProviderIds", {}).get("Tmdb"),
                "imdb_id": item.get("ProviderIds", {}).get("Imdb"),
                "size": self.format_size(item.get("Size", 0)) if item.get("Size") else None,
                "item_id": item.get("Id"),
                "item_type": item.get("Type"),
            })
        
        # 标记事件（包括播放标记、评分、收藏）
        elif event.startswith("item.mark") or event.startswith("user.rating") or event.startswith("item.rating") or event.startswith("user.favorite") or event.startswith("item.favorite") or event == "item.rate":
            item = response.get("Item", {})
            if not item:
                return None
            
            media_type = "电影" if item.get("Type") == "Movie" else "剧集"
            media_name = item.get("Name", "未知媒体")
            
            if item.get("Type") == "Episode":
                series_name = item.get("SeriesName", "未知剧集")
                season_num = item.get("ParentIndexNumber", 0)
                episode_num = item.get("IndexNumber", 0)
                media_name = f"{series_name} S{season_num}E{episode_num} - {media_name}"
            
            context.update({
                "media_type": media_type,
                "item_name": media_name,
                "item_year": item.get("ProductionYear"),
                "overview": item.get("Overview", ""),
                "rating": item.get("CommunityRating"),
                "tmdb_id": item.get("ProviderIds", {}).get("Tmdb"),
                "imdb_id": item.get("ProviderIds", {}).get("Imdb"),
                "item_id": item.get("Id"),
                "item_type": item.get("Type"),
            })
        
        return context
