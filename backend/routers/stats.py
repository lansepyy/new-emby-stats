"""
统计相关路由模块
处理所有统计数据的 API 端点
"""
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional, List

from database import (
    get_playback_db,
    get_count_expr,
    get_duration_filter,
    local_datetime,
    local_date
)
from services.users import user_service
from services.emby import emby_service
from name_mappings import name_mapping_service

router = APIRouter(prefix="/api", tags=["stats"])


def build_filter_conditions(
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    users: Optional[List[str]] = None,
    clients: Optional[List[str]] = None,
    devices: Optional[List[str]] = None,
    item_types: Optional[List[str]] = None,
    playback_methods: Optional[List[str]] = None,
    search: Optional[str] = None,
) -> tuple[str, list]:
    """
    构建通用的筛选条件
    返回 (WHERE 子句部分, 参数列表)
    """
    conditions = []
    params = []
    date_col = local_date("DateCreated")

    # 日期范围筛选
    if start_date and end_date:
        conditions.append(f"{date_col} >= date(?) AND {date_col} <= date(?)")
        params.extend([start_date, end_date])
    elif start_date:
        conditions.append(f"{date_col} >= date(?)")
        params.append(start_date)
    elif end_date:
        conditions.append(f"{date_col} <= date(?)")
        params.append(end_date)
    elif days:
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        conditions.append(f"{date_col} >= date(?)")
        params.append(since_date)

    # 用户筛选
    if users and len(users) > 0:
        placeholders = ",".join(["?" for _ in users])
        conditions.append(f"UserId IN ({placeholders})")
        params.extend(users)

    # 客户端筛选
    if clients and len(clients) > 0:
        placeholders = ",".join(["?" for _ in clients])
        conditions.append(f"ClientName IN ({placeholders})")
        params.extend(clients)

    # 设备筛选
    if devices and len(devices) > 0:
        placeholders = ",".join(["?" for _ in devices])
        conditions.append(f"DeviceName IN ({placeholders})")
        params.extend(devices)

    # 媒体类型筛选
    if item_types and len(item_types) > 0:
        placeholders = ",".join(["?" for _ in item_types])
        conditions.append(f"ItemType IN ({placeholders})")
        params.extend(item_types)

    # 播放方式筛选
    if playback_methods and len(playback_methods) > 0:
        placeholders = ",".join(["?" for _ in playback_methods])
        conditions.append(f"PlaybackMethod IN ({placeholders})")
        params.extend(playback_methods)

    # 搜索关键词筛选
    if search and search.strip():
        conditions.append("ItemName LIKE ?")
        params.append(f"%{search.strip()}%")

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params


@router.get("/overview")
async def get_overview(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYY-MM-DD"),
    users: Optional[str] = Query(default=None, description="用户ID列表，逗号分隔"),
    clients: Optional[str] = Query(default=None, description="客户端列表，逗号分隔"),
    devices: Optional[str] = Query(default=None, description="设备列表，逗号分隔"),
    item_types: Optional[str] = Query(default=None, description="媒体类型列表，逗号分隔"),
    playback_methods: Optional[str] = Query(default=None, description="播放方式列表，逗号分隔"),
):
    """获取总览统计"""
    user_map = await user_service.get_user_map()

    # 解析逗号分隔的列表参数
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    async with get_playback_db() as db:
        count_expr = get_count_expr()

        # 总播放次数（只计满足时长的）和时长（统计所有）
        async with db.execute(f"""
            SELECT
                {count_expr} as total_plays,
                COALESCE(SUM(PlayDuration), 0) as total_duration,
                COUNT(DISTINCT UserId) as unique_users,
                COUNT(DISTINCT ItemId) as unique_items
            FROM PlaybackActivity
            WHERE {where_clause}
        """, params) as cursor:
            row = await cursor.fetchone()
            total_plays = int(row[0] or 0)
            total_duration = row[1]
            unique_users = row[2]
            unique_items = row[3]

        # 按类型统计
        async with db.execute(f"""
            SELECT ItemType, {count_expr} as count, COALESCE(SUM(PlayDuration), 0) as duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY ItemType
        """, params) as cursor:
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
async def get_trend(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    item_types: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取播放趋势（按天）"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                {date_col} as play_date,
                {count_expr} as plays,
                COALESCE(SUM(PlayDuration), 0) as duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY {date_col}
            ORDER BY play_date
        """, params) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "date": row[0],
                    "plays": int(row[1] or 0),
                    "duration_hours": round(row[2] / 3600, 2)
                })

    return {"trend": data}


@router.get("/users")
async def get_user_stats(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    item_types: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取用户统计"""
    user_map = await user_service.get_user_map()

    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    count_expr = get_count_expr()
    datetime_col = local_datetime("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                UserId,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration,
                MAX({datetime_col}) as last_play
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY UserId
            ORDER BY total_duration DESC
        """, params) as cursor:
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
async def get_client_stats(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    item_types: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取客户端统计"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    count_expr = get_count_expr()

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                ClientName,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY ClientName
            ORDER BY play_count DESC
        """, params) as cursor:
            # 使用字典合并同名映射后的客户端
            merged_data = {}
            async for row in cursor:
                original_name = row[0] or "Unknown"
                mapped_name = name_mapping_service.map_client_name(original_name)
                play_count = int(row[1] or 0)
                duration = row[2]

                if mapped_name in merged_data:
                    merged_data[mapped_name]["play_count"] += play_count
                    merged_data[mapped_name]["duration"] += duration
                else:
                    merged_data[mapped_name] = {
                        "play_count": play_count,
                        "duration": duration
                    }

            # 转换为列表并按播放次数排序
            data = [
                {
                    "client": name,
                    "play_count": info["play_count"],
                    "duration_hours": round(info["duration"] / 3600, 2)
                }
                for name, info in sorted(
                    merged_data.items(),
                    key=lambda x: x[1]["play_count"],
                    reverse=True
                )
            ]

    return {"clients": data}


@router.get("/devices")
async def get_device_stats(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    item_types: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取设备统计"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    count_expr = get_count_expr()

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                DeviceName,
                ClientName,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY DeviceName
            ORDER BY play_count DESC
        """, params) as cursor:
            # 使用字典合并同名映射后的设备
            merged_data = {}
            async for row in cursor:
                original_device = row[0] or "Unknown"
                original_client = row[1] or "Unknown"
                mapped_device = name_mapping_service.map_device_name(original_device)
                mapped_client = name_mapping_service.map_client_name(original_client)
                play_count = int(row[2] or 0)
                duration = row[3]

                # 使用设备名作为 key 进行合并
                if mapped_device in merged_data:
                    merged_data[mapped_device]["play_count"] += play_count
                    merged_data[mapped_device]["duration"] += duration
                else:
                    merged_data[mapped_device] = {
                        "client": mapped_client,
                        "play_count": play_count,
                        "duration": duration
                    }

            # 转换为列表并按播放次数排序
            data = [
                {
                    "device": name,
                    "client": info["client"],
                    "play_count": info["play_count"],
                    "duration_hours": round(info["duration"] / 3600, 2)
                }
                for name, info in sorted(
                    merged_data.items(),
                    key=lambda x: x[1]["play_count"],
                    reverse=True
                )
            ]

    return {"devices": data}


@router.get("/playback-methods")
async def get_playback_methods(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    item_types: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取播放方式统计"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    count_expr = get_count_expr()

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                PlaybackMethod,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY PlaybackMethod
            ORDER BY play_count DESC
        """, params) as cursor:
            data = []
            async for row in cursor:
                data.append({
                    "method": row[0] or "Unknown",
                    "play_count": int(row[1] or 0),
                    "duration_hours": round(row[2] / 3600, 2)
                })

    return {"methods": data}


@router.get("/hourly")
async def get_hourly_stats(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    item_types: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取按小时统计（热力图数据）"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    type_list = [t.strip() for t in item_types.split(",")] if item_types else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=type_list,
        playback_methods=method_list,
    )

    count_expr = get_count_expr()
    datetime_col = local_datetime("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                strftime('%w', {datetime_col}) as day_of_week,
                strftime('%H', {datetime_col}) as hour,
                {count_expr} as play_count
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY day_of_week, hour
        """, params) as cursor:
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
            "device_name": name_mapping_service.map_device_name(session.get("DeviceName", "Unknown")),
            "client": name_mapping_service.map_client_name(session.get("Client", "Unknown")),
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
async def get_recent_plays(
    limit: int = Query(default=20, ge=1, le=100),
    days: Optional[int] = Query(default=None, ge=1, le=365, description="天数范围，不传则查询全部"),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYY-MM-DD"),
    users: Optional[str] = Query(default=None, description="用户ID列表，逗号分隔"),
    clients: Optional[str] = Query(default=None, description="客户端列表，逗号分隔"),
    devices: Optional[str] = Query(default=None, description="设备列表，逗号分隔"),
    item_types: Optional[str] = Query(default=None, description="媒体类型列表，逗号分隔"),
    playback_methods: Optional[str] = Query(default=None, description="播放方式列表，逗号分隔"),
    search: Optional[str] = Query(default=None, description="搜索关键词，匹配内容名称"),
):
    """获取最近播放记录"""
    user_map = await user_service.get_user_map()
    datetime_col = local_datetime("DateCreated")

    # 解析筛选参数
    user_list = users.split(",") if users else None
    client_list = clients.split(",") if clients else None
    device_list = devices.split(",") if devices else None
    item_type_list = item_types.split(",") if item_types else None
    playback_method_list = playback_methods.split(",") if playback_methods else None

    # 构建筛选条件
    where_clause, params = build_filter_conditions(
        days=days if not start_date and not end_date else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=item_type_list,
        playback_methods=playback_method_list,
        search=search,
    )

    # 添加 limit 参数
    params.append(limit)

    # 获取播放时长过滤条件
    duration_filter = get_duration_filter()

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
            WHERE {where_clause}{duration_filter}
            ORDER BY DateCreated DESC
            LIMIT ?
        """, params) as cursor:
            data = []
            async for row in cursor:
                user_id = row[1] or ""
                item_id = row[2]
                item_name = row[3]
                item_type = row[4]

                username = user_service.match_username(user_id, user_map)

                # 获取海报和背景图
                info = await emby_service.get_item_info(str(item_id))
                poster_url = emby_service.get_poster_url(str(item_id), item_type, info)
                backdrop_url = emby_service.get_backdrop_url(str(item_id), item_type, info)

                # 提取剧名
                show_name = item_name.split(" - ")[0] if " - " in item_name else item_name

                # 获取单集简介（如果有）
                overview = info.get("Overview", "") if info else ""

                # 如果是剧集且没有 backdrop，尝试从剧集获取
                if item_type == "Episode" and not backdrop_url and info:
                    series_id = info.get("SeriesId")
                    if series_id:
                        series_info = await emby_service.get_item_info(series_id)
                        if series_info and series_info.get("BackdropImageTags"):
                            backdrop_url = f"/api/backdrop/{series_id}"

                data.append({
                    "time": row[0],
                    "username": username,
                    "item_id": item_id,
                    "item_name": item_name,
                    "show_name": show_name,
                    "item_type": item_type,
                    "client": name_mapping_service.map_client_name(row[5]),
                    "device": name_mapping_service.map_device_name(row[6]),
                    "duration_minutes": round((row[7] or 0) / 60, 1),
                    "method": row[8],
                    "poster_url": poster_url,
                    "backdrop_url": backdrop_url,
                    "overview": overview
                })

    return {"recent": data}


@router.get("/filter-options")
async def get_filter_options():
    """获取所有可用的筛选选项"""
    user_map = await user_service.get_user_map()

    async with get_playback_db() as db:
        # 获取所有用户
        async with db.execute("""
            SELECT DISTINCT UserId FROM PlaybackActivity WHERE UserId IS NOT NULL
        """) as cursor:
            user_ids = []
            async for row in cursor:
                user_id = row[0]
                if user_id:
                    username = user_service.match_username(user_id, user_map)
                    user_ids.append({"id": user_id, "name": username})

        # 获取所有客户端（返回原始名称和映射后名称）
        async with db.execute("""
            SELECT DISTINCT ClientName FROM PlaybackActivity WHERE ClientName IS NOT NULL ORDER BY ClientName
        """) as cursor:
            clients = []
            seen_mapped = set()
            for row in await cursor.fetchall():
                if row[0]:
                    original = row[0]
                    mapped = name_mapping_service.map_client_name(original)
                    # 去重：如果映射后名称已存在则跳过
                    if mapped not in seen_mapped:
                        clients.append({
                            "original": original,
                            "display": mapped
                        })
                        seen_mapped.add(mapped)

        # 获取所有设备（返回原始名称和映射后名称）
        async with db.execute("""
            SELECT DISTINCT DeviceName FROM PlaybackActivity WHERE DeviceName IS NOT NULL ORDER BY DeviceName
        """) as cursor:
            devices = []
            seen_mapped = set()
            for row in await cursor.fetchall():
                if row[0]:
                    original = row[0]
                    mapped = name_mapping_service.map_device_name(original)
                    # 去重：如果映射后名称已存在则跳过
                    if mapped not in seen_mapped:
                        devices.append({
                            "original": original,
                            "display": mapped
                        })
                        seen_mapped.add(mapped)

        # 获取所有媒体类型
        async with db.execute("""
            SELECT DISTINCT ItemType FROM PlaybackActivity WHERE ItemType IS NOT NULL ORDER BY ItemType
        """) as cursor:
            item_types = [row[0] for row in await cursor.fetchall() if row[0]]

        # 获取所有播放方式
        async with db.execute("""
            SELECT DISTINCT PlaybackMethod FROM PlaybackActivity WHERE PlaybackMethod IS NOT NULL ORDER BY PlaybackMethod
        """) as cursor:
            playback_methods = [row[0] for row in await cursor.fetchall() if row[0]]

        # 获取日期范围
        async with db.execute("""
            SELECT MIN(date(DateCreated)), MAX(date(DateCreated)) FROM PlaybackActivity
        """) as cursor:
            row = await cursor.fetchone()
            date_range = {
                "min": row[0] if row else None,
                "max": row[1] if row else None
            }

    return {
        "users": user_ids,
        "clients": clients,
        "devices": devices,
        "item_types": item_types,
        "playback_methods": playback_methods,
        "date_range": date_range
    }


@router.get("/name-mappings")
async def get_name_mappings():
    """获取名称映射配置"""
    return name_mapping_service.get_all_mappings()


@router.post("/name-mappings")
async def save_name_mappings(mappings: dict):
    """保存名称映射配置"""
    success = name_mapping_service.save_mappings(mappings)
    if success:
        return {"status": "ok", "message": "映射配置已保存"}
    else:
        return {"status": "error", "message": "保存失败"}


@router.post("/name-mappings/reload")
async def reload_name_mappings():
    """重新加载名称映射配置"""
    name_mapping_service.reload()
    return {"status": "ok", "message": "配置已重新加载"}
