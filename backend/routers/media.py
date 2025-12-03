"""
媒体相关路由模块
处理内容排行和海报等 API 端点
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from database import get_playback_db, get_count_expr, local_date
from services.emby import emby_service

router = APIRouter(prefix="/api", tags=["media"])


@router.get("/top-content")
async def get_top_content(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    item_type: Optional[str] = Query(default=None)
):
    """获取热门内容排行（剧集按剧名聚合，电影等按ItemId）"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        # 先查询所有符合条件的播放记录
        query = f"""
            SELECT
                ItemId,
                ItemName,
                ItemType,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?)
        """
        params = [since_date]

        if item_type:
            query += " AND ItemType = ?"
            params.append(item_type)

        query += " GROUP BY ItemId"

        async with db.execute(query, params) as cursor:
            # 按剧名/内容聚合
            content_map = defaultdict(lambda: {
                "play_count": 0,
                "duration": 0,
                "item_id": None,
                "item_type": None,
                "full_name": None
            })

            async for row in cursor:
                item_id = row[0]
                item_name = row[1] or "Unknown"
                item_type_val = row[2]
                play_count = int(row[3] or 0)
                duration = row[4]

                # 对于剧集，提取剧名作为聚合key；其他类型用完整名称
                if item_type_val == "Episode" and " - " in item_name:
                    key = item_name.split(" - ")[0]  # 剧名
                else:
                    key = item_name

                content_map[key]["play_count"] += play_count
                content_map[key]["duration"] += duration

                # 保存一个item_id用于获取海报
                if not content_map[key]["item_id"]:
                    content_map[key]["item_id"] = item_id
                    content_map[key]["item_type"] = item_type_val
                    content_map[key]["full_name"] = item_name

        # 排序并限制数量
        sorted_content = sorted(
            content_map.items(),
            key=lambda x: x[1]["play_count"],
            reverse=True
        )[:limit]

        data = []
        for name, info in sorted_content:
            item_id = info["item_id"]
            item_type_val = info["item_type"]

            # 获取海报 URL 和剧集介绍
            item_info = await emby_service.get_item_info(str(item_id))
            poster_url = emby_service.get_poster_url(str(item_id), item_type_val, item_info)

            # 获取 overview（剧集介绍）
            overview = item_info.get("Overview", "") if item_info else ""
            # 如果是单集，尝试获取剧集总介绍
            if item_type_val == "Episode" and item_info:
                series_id = item_info.get("SeriesId")
                if series_id:
                    series_info = await emby_service.get_item_info(series_id)
                    if series_info:
                        overview = series_info.get("Overview", overview)

            data.append({
                "item_id": item_id,
                "name": info["full_name"] or name,
                "show_name": name,
                "type": item_type_val,
                "play_count": info["play_count"],
                "duration_hours": round(info["duration"] / 3600, 2),
                "poster_url": poster_url,
                "overview": overview
            })

    return {"top_content": data}


@router.get("/top-shows")
async def get_top_shows(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50)
):
    """获取热门剧集（按剧名聚合）"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    count_expr = get_count_expr()
    date_col = local_date("DateCreated")

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                ItemId,
                ItemName,
                ItemType,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {date_col} >= date(?) AND ItemType = 'Episode'
            GROUP BY ItemId
        """, (since_date,)) as cursor:
            shows = defaultdict(lambda: {
                "play_count": 0,
                "duration": 0,
                "episodes": set(),
                "series_id": None,
                "item_id": None
            })
            async for row in cursor:
                item_id = row[0]
                item_name = row[1] or "Unknown"
                show_name = item_name.split(" - ")[0] if " - " in item_name else item_name
                shows[show_name]["play_count"] += int(row[3] or 0)
                shows[show_name]["duration"] += row[4]
                shows[show_name]["episodes"].add(item_name)
                # 保存一个 item_id 用于获取 series_id
                if not shows[show_name]["item_id"]:
                    shows[show_name]["item_id"] = item_id

    # 排序并限制数量
    sorted_shows = sorted(shows.items(), key=lambda x: x[1]["play_count"], reverse=True)[:limit]

    result = []
    for show_name, data in sorted_shows:
        # 获取海报和剧集介绍
        poster_url = None
        overview = ""
        if data["item_id"]:
            info = await emby_service.get_item_info(str(data["item_id"]))
            if info and info.get("SeriesId"):
                poster_url = f"/api/poster/{info['SeriesId']}"
                # 获取剧集总介绍
                series_info = await emby_service.get_item_info(info["SeriesId"])
                if series_info:
                    overview = series_info.get("Overview", "")

        result.append({
            "show_name": show_name,
            "play_count": data["play_count"],
            "duration_hours": round(data["duration"] / 3600, 2),
            "episode_count": len(data["episodes"]),
            "poster_url": poster_url,
            "overview": overview
        })

    return {"top_shows": result}


@router.get("/poster/{item_id}")
async def get_poster(
    item_id: str,
    maxHeight: int = Query(default=300),
    maxWidth: int = Query(default=200)
):
    """代理获取 Emby 海报图片"""
    content, content_type = await emby_service.get_poster(item_id, maxHeight, maxWidth)

    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"} if content else {}
    )
