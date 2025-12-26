"""
观影报告服务
生成和发送观影统计报告
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import get_playback_db, get_count_expr
from services.users import user_service
from services.emby import EmbyService
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """报告生成服务"""
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日报告（昨天的数据）"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return await self._generate_report(
            start_date=yesterday,
            end_date=yesterday,
            title="📊 每日观影报告",
            period=f"{yesterday}"
        )
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        """生成每周报告（过去7天）"""
        today = datetime.now()
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        return await self._generate_report(
            start_date=start_date,
            end_date=end_date,
            title="📊 每周观影报告",
            period=f"{start_date} 至 {end_date}"
        )
    
    async def generate_monthly_report(self) -> Dict[str, Any]:
        """生成每月报告（过去30天）"""
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        return await self._generate_report(
            start_date=start_date,
            end_date=end_date,
            title="📊 每月观影报告",
            period=f"{start_date} 至 {end_date}"
        )
    
    async def _generate_report(
        self,
        start_date: str,
        end_date: str,
        title: str,
        period: str
    ) -> Dict[str, Any]:
        """生成报告核心逻辑"""
        async with get_playback_db() as db:
            count_expr = get_count_expr()
            
            # 1. 总播放次数和时长
            total_query = f"""
                SELECT 
                    {count_expr} as play_count,
                    COALESCE(SUM(PlayDuration), 0) as total_duration
                FROM PlaybackActivity
                WHERE date(DateCreated) >= date(?) AND date(DateCreated) <= date(?)
            """
            
            async with db.execute(total_query, [start_date, end_date]) as cursor:
                row = await cursor.fetchone()
                total_plays = int(row[0] or 0)
                total_duration = int(row[1] or 0)
                total_hours = round(total_duration / 3600, 1)
            
            # 2. 热门内容 Top 5（需要获取ItemId）
            top_content_query = f"""
                SELECT 
                    ItemName,
                    ItemType,
                    ItemId,
                    {count_expr} as play_count,
                    COALESCE(SUM(PlayDuration), 0) / 3600.0 as hours
                FROM PlaybackActivity
                WHERE date(DateCreated) >= date(?) AND date(DateCreated) <= date(?)
                GROUP BY ItemId
                ORDER BY play_count DESC
                LIMIT 5
            """
            
            top_content = []
            emby_service = EmbyService()
            async with db.execute(top_content_query, [start_date, end_date]) as cursor:
                async for row in cursor:
                    item_id = row[2]
                    item_type = row[1] or "未知"
                    
                    # 从Emby获取TMDB ID
                    tmdb_id = None
                    series_tmdb_id = None
                    try:
                        item_info = await emby_service.get_item_info(item_id)
                        if item_info:
                            provider_ids = item_info.get("ProviderIds", {})
                            # 如果是剧集，只使用SeriesId的TMDB ID（不使用集的TMDB ID）
                            if item_type == "Episode":
                                series_id = item_info.get("SeriesId")
                                if series_id:
                                    series_info = await emby_service.get_item_info(series_id)
                                    if series_info:
                                        series_tmdb_id = series_info.get("ProviderIds", {}).get("Tmdb")
                            else:
                                # 电影等其他类型使用自己的TMDB ID
                                tmdb_id = provider_ids.get("Tmdb")
                    except Exception as e:
                        logger.warning(f"获取TMDB ID失败 (item_id={item_id}): {e}")
                    
                    top_content.append({
                        "name": row[0] or "未知",
                        "type": item_type,
                        "item_id": item_id,
                        "play_count": int(row[3] or 0),
                        "hours": round(row[4] or 0, 1),
                        "tmdb_id": tmdb_id,
                        "series_tmdb_id": series_tmdb_id
                    })
            
            # 3. 活跃用户 Top 5
            top_users_query = f"""
                SELECT 
                    UserId,
                    {count_expr} as play_count,
                    COALESCE(SUM(PlayDuration), 0) / 3600.0 as hours
                FROM PlaybackActivity
                WHERE date(DateCreated) >= date(?) AND date(DateCreated) <= date(?)
                  AND UserId IS NOT NULL
                GROUP BY UserId
                ORDER BY play_count DESC
                LIMIT 5
            """
            
            top_users = []
            user_map = await user_service.get_user_map()
            async with db.execute(top_users_query, [start_date, end_date]) as cursor:
                async for row in cursor:
                    user_id = row[0]
                    username = user_service.match_username(user_id, user_map)
                    top_users.append({
                        "username": username,
                        "play_count": int(row[1] or 0),
                        "hours": round(row[2] or 0, 1)
                    })
            
            # 4. 按类型统计
            type_stats_query = f"""
                SELECT 
                    ItemType,
                    {count_expr} as play_count
                FROM PlaybackActivity
                WHERE date(DateCreated) >= date(?) AND date(DateCreated) <= date(?)
                  AND ItemType IS NOT NULL
                GROUP BY ItemType
                ORDER BY play_count DESC
            """
            
            type_stats = []
            async with db.execute(type_stats_query, [start_date, end_date]) as cursor:
                async for row in cursor:
                    type_stats.append({
                        "type": row[0] or "未知",
                        "count": int(row[1] or 0)
                    })
            
            return {
                "title": title,
                "period": period,
                "summary": {
                    "total_plays": total_plays,
                    "total_hours": total_hours
                },
                "top_content": top_content,
                "top_users": top_users,
                "type_stats": type_stats
            }
    
    async def get_cover_images(self, report: Dict[str, Any], emby_server: str) -> List[Optional[bytes]]:
        """获取热门内容的封面图片
        
        Args:
            report: 报告数据
            emby_server: Emby服务器地址
        
        Returns:
            封面图片字节列表
        """
        import httpx
        
        images = []
        top_content = report.get('top_content', [])[:5]
        
        async with httpx.AsyncClient() as client:
            for item in top_content:
                item_id = item.get('item_id')
                if not item_id or not emby_server:
                    images.append(None)
                    continue
                
                try:
                    # 尝试获取Primary图片
                    image_url = f"{emby_server}/Items/{item_id}/Images/Primary?maxWidth=200&quality=90"
                    response = await client.get(image_url, timeout=10)
                    
                    if response.status_code == 200:
                        images.append(response.content)
                        logger.info(f"成功获取封面: {item['name']}")
                    else:
                        images.append(None)
                        logger.warning(f"封面获取失败: {item['name']}, HTTP {response.status_code}")
                
                except Exception as e:
                    logger.warning(f"封面下载异常: {item['name']}, {e}")
                    images.append(None)
        
        return images
    
    def format_report_text(self, report: Dict[str, Any]) -> str:
        """将报告格式化为文本"""
        lines = []
        lines.append(f"📊 {report['title']}")
        lines.append(f"📅 统计周期：{report['period']}")
        lines.append("")
        lines.append(f"📈 总览")
        lines.append(f"  播放次数：{report['summary']['total_plays']} 次")
        lines.append(f"  观影时长：{report['summary']['total_hours']} 小时")
        lines.append("")
        
        if report['top_content']:
            lines.append("🎬 热门内容 Top 5")
            for i, item in enumerate(report['top_content'], 1):
                lines.append(f"  {i}. {item['name']} ({item['type']})")
                lines.append(f"     播放 {item['play_count']} 次 | {item['hours']} 小时")
            lines.append("")
        
        if report['top_users']:
            lines.append("👥 活跃用户 Top 5")
            for i, user in enumerate(report['top_users'], 1):
                lines.append(f"  {i}. {user['username']}")
                lines.append(f"     播放 {user['play_count']} 次 | {user['hours']} 小时")
            lines.append("")
        
        if report['type_stats']:
            lines.append("📺 内容类型统计")
            for stat in report['type_stats']:
                lines.append(f"  {stat['type']}: {stat['count']} 次")
        
        return "\n".join(lines)


report_service = ReportService()
