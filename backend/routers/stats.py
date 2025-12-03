"""
统计相关路由模块
处理所有统计数据的 API 端点
"""
from fastapi import APIRouter, Query
from datetime import datetime, timedelta

from database import (
    get_playback_db,
    get_count_expr,
    get_duration_filter,
    local_datetime,
    local_date
)
from services.users import user_service
from services.emby import emby_service

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/overview")
async def get_overview(days: int = Query(default=30, ge=1, le=365)):
    """获取总览统计"""
    user_map = await user_service.get_user_map()
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    async with get_playback_db() as db:
        count_expr = get_count_expr()
        date_col = local_date("DateCreated")

        # 总播放次数（只计满足时长的）和时长（统计所有）
        async with db.execute(f"""
            SELECT
                {count_expr} as total_plays,
                COALESCE(SUM(PlayDuration), 0) as total_duration,
                COUNT(DISTINCT UserId) as unique_users,
                COUNT(DISTINCT ItemId) as unique_items
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
        """, (since_date,)) as cursor:
            row = await cursor.fetchone()
            total_plays = int(row[0] or 0)
            total_duration = row[1]
            unique_users = row[2]
            unique_items = row[3]

        # 按类型统计
        async with db.execute(f"""
            SELECT ItemType, {count_expr} as count, COALESCE(SUM(PlayDuration), 0) as duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY ItemType
        """, (since_date,)) as cursor:
            by_type = {}
            async for row in cursor:
                by_type[row[0] or "Unknown"] = {"count": int(row[1] or 0), "duration": row[2]}

    return {
        "total_plays": total_plays,
        "total_duration_seconds": total_duration,
        "total_duration_hours": round(total_duration / 3600, 2),
        "unique_users": unique_users,
        "unique_items": unique_items,
        "by_type": by_type,
        "days": days
    }


@router.get("/trend")
async def get_trend(days: int = Query(default=30, ge=1, le=365)):
    """获取播放趋势（按天）"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                {date_col} as play_date,
                {count_expr} as plays,
                COALESCE(SUM(PlayDuration), 0) as duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY {date_col}
            ORDER BY play_date
        """, (since_date,)) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "date": row[0],
                    "plays": int(row[1] or 0),
                    "duration_hours": round(row[2] / 3600, 2)
                })

    return {"trend": data}


@router.get("/users")
async def get_user_stats(days: int = Query(default=30, ge=1, le=365)):
    """获取用户统计"""
    user_map = await user_service.get_user_map()
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")
    datetime_col = local_datetime("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                UserId,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration,
                MAX({datetime_col}) as last_play
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY UserId
            ORDER BY total_duration DESC
        """, (since_date,)) as cursor:
            data = []
            async for row in cursor:
                user_id = row[0] or ""
                username = user_service.match_username(user_id, user_map)

                data.append({
                    "user_id": user_id,
                    "username": username,
                    "play_count": int(row[1] or 0),
                    "duration_hours": round(row[2] / 3600, 2),
                    "last_play": row[3]
                })

    return {"users": data}


@router.get("/clients")
async def get_client_stats(days: int = Query(default=30, ge=1, le=365)):
    """获取客户端统计"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                ClientName,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY ClientName
            ORDER BY play_count DESC
        """, (since_date,)) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "client": row[0] or "Unknown",
                    "play_count": int(row[1] or 0),
                    "duration_hours": round(row[2] / 3600, 2)
                })

    return {"clients": data}


@router.get("/devices")
async def get_device_stats(days: int = Query(default=30, ge=1, le=365)):
    """获取设备统计"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                DeviceName,
                ClientName,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY DeviceName
            ORDER BY play_count DESC
        """, (since_date,)) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "device": row[0] or "Unknown",
                    "client": row[1] or "Unknown",
                    "play_count": int(row[2] or 0),
                    "duration_hours": round(row[3] / 3600, 2)
                })

    return {"devices": data}


@router.get("/playback-methods")
async def get_playback_methods(days: int = Query(default=30, ge=1, le=365)):
    """获取播放方式统计"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                PlaybackMethod,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY PlaybackMethod
            ORDER BY play_count DESC
        """, (since_date,)) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "method": row[0] or "Unknown",
                    "play_count": int(row[1] or 0),
                    "duration_hours": round(row[2] / 3600, 2)
                })

    return {"methods": data}


@router.get("/hourly")
async def get_hourly_stats(days: int = Query(default=30, ge=1, le=365)):
    """获取按小时统计（热力图数据）"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")
    datetime_col = local_datetime("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                strftime('%w', {datetime_col}) as day_of_week,
                strftime('%H', {datetime_col}) as hour,
                {count_expr} as play_count
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
            GROUP BY day_of_week, hour
        """, (since_date,)) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "day": int(row[0]),  # 0=Sunday, 1=Monday, ...
                    "hour": int(row[1]),
                    "count": int(row[2] or 0)
                })

    return {"hourly": data}


@router.get("/now-playing")
async def get_now_playing():
    """获取当前正在播放的内容"""
    user_map = await user_service.get_user_map()
    sessions = await emby_service.get_now_playing()

    data = []
    for session in sessions:
        item = session.get("NowPlayingItem", {})
        user_name = session.get("UserName", "Unknown")
        user_id = session.get("UserId", "")

        # 尝试从 user_map 匹配用户名
        if user_id:
            matched = user_service.match_username(user_id, user_map)
            if matched != user_id[:8]:
                user_name = matched

        item_id = item.get("Id", "")
        item_name = item.get("Name", "Unknown")
        item_type = item.get("Type", "")
        series_name = item.get("SeriesName", "")

        # 获取海报
        poster_url = None
        if item_type == "Episode" and item.get("SeriesId"):
            poster_url = f"/api/poster/{item['SeriesId']}"
        elif item.get("ImageTags", {}).get("Primary"):
            poster_url = f"/api/poster/{item_id}"

        # 构建显示名称
        if series_name:
            display_name = f"{series_name} - {item_name}"
        else:
            display_name = item_name

        # 播放进度
        position_ticks = session.get("PlayState", {}).get("PositionTicks", 0)
        runtime_ticks = item.get("RunTimeTicks", 0)
        progress = 0
        if runtime_ticks > 0:
            progress = round(position_ticks / runtime_ticks * 100, 1)

        # 播放时长（已播放）
        position_seconds = position_ticks // 10000000 if position_ticks else 0
        runtime_seconds = runtime_ticks // 10000000 if runtime_ticks else 0

        data.append({
            "user_name": user_name,
            "device_name": session.get("DeviceName", "Unknown"),
            "client": session.get("Client", "Unknown"),
            "item_id": item_id,
            "item_name": display_name,
            "item_type": item_type,
            "poster_url": poster_url,
            "progress": progress,
            "position_seconds": position_seconds,
            "runtime_seconds": runtime_seconds,
            "is_paused": session.get("PlayState", {}).get("IsPaused", False),
            "play_method": session.get("PlayState", {}).get("PlayMethod", ""),
        })

    return {"now_playing": data, "count": len(data)}


@router.get("/recent")
async def get_recent_plays(limit: int = Query(default=20, ge=1, le=100)):
    """获取最近播放记录"""
    user_map = await user_service.get_user_map()
    duration_filter = get_duration_filter()
    datetime_col = local_datetime("DateCreated")
    # 去掉开头的 " AND "
    where_clause = f"WHERE {duration_filter[5:]}" if duration_filter else ""

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                {datetime_col} as LocalTime,
                UserId,
                ItemId,
                ItemName,
                ItemType,
                ClientName,
                DeviceName,
                PlayDuration,
                PlaybackMethod
            FROM PlaybackActivity
            {where_clause}
            ORDER BY DateCreated DESC
            LIMIT ?
        """, (limit,)) as cursor:
            data = []
            async for row in cursor:
                user_id = row[1] or ""
                item_id = row[2]
                item_name = row[3]
                item_type = row[4]

                username = user_service.match_username(user_id, user_map)

                # 获取海报
                info = await emby_service.get_item_info(str(item_id))
                poster_url = emby_service.get_poster_url(str(item_id), item_type, info)

                # 提取剧名
                show_name = item_name.split(" - ")[0] if " - " in item_name else item_name

                # 获取单集简介（如果有）
                overview = info.get("Overview", "") if info else ""

                data.append({
                    "time": row[0],
                    "username": username,
                    "item_id": item_id,
                    "item_name": item_name,
                    "show_name": show_name,
                    "item_type": item_type,
                    "client": row[5],
                    "device": row[6],
                    "duration_minutes": round((row[7] or 0) / 60, 1),
                    "method": row[8],
                    "poster_url": poster_url,
                    "overview": overview
                })

    return {"recent": data}
