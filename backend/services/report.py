"""
观影报告服务
生成和发送观影统计报告
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import get_playback_db, get_count_expr
from services.emby import emby_service


class ReportService:
    """报告生成服务"""
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日报告（昨天的数据）"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return await self._generate_report(
            start_date=yesterday,
            end_date=yesterday,
            title="每日观影报告",
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
            title="每周观影报告",
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
            title="每月观影报告",
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
            
            # 2. 热门内容 Top 5
            top_content_query = f"""
                SELECT 
                    ItemName,
                    ItemType,
                    {count_expr} as play_count,
                    COALESCE(SUM(PlayDuration), 0) / 3600.0 as hours
                FROM PlaybackActivity
                WHERE date(DateCreated) >= date(?) AND date(DateCreated) <= date(?)
                GROUP BY ItemId
                ORDER BY play_count DESC
                LIMIT 5
            """
            
            top_content = []
            async with db.execute(top_content_query, [start_date, end_date]) as cursor:
                async for row in cursor:
                    top_content.append({
                        "name": row[0] or "未知",
                        "type": row[1] or "未知",
                        "play_count": int(row[2] or 0),
                        "hours": round(row[3] or 0, 1)
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
            async with db.execute(top_users_query, [start_date, end_date]) as cursor:
                async for row in cursor:
                    user_id = row[0]
                    user_info = await emby_service.get_user_info(user_id)
                    username = user_info.get("Name", user_id) if user_info else user_id
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
