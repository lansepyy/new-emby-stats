"""
媒体相关路由模块
处理内容排行和海报等 API 端点
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List
import httpx
import logging

from database import get_playback_db, get_count_expr, local_date
from services.emby import emby_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["media"])


def build_filter_conditions(
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    users: Optional[List[str]] = None,
    clients: Optional[List[str]] = None,
    devices: Optional[List[str]] = None,
    item_types: Optional[List[str]] = None,
    playback_methods: Optional[List[str]] = None,
) -> tuple[str, list]:
    """构建通用的筛选条件"""
    conditions = []
    params = []
    date_col = local_date("DateCreated")

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

    if users and len(users) > 0:
        placeholders = ",".join(["?" for _ in users])
        conditions.append(f"UserId IN ({placeholders})")
        params.extend(users)

    if clients and len(clients) > 0:
        placeholders = ",".join(["?" for _ in clients])
        conditions.append(f"ClientName IN ({placeholders})")
        params.extend(clients)

    if devices and len(devices) > 0:
        placeholders = ",".join(["?" for _ in devices])
        conditions.append(f"DeviceName IN ({placeholders})")
        params.extend(devices)

    if item_types and len(item_types) > 0:
        placeholders = ",".join(["?" for _ in item_types])
        conditions.append(f"ItemType IN ({placeholders})")
        params.extend(item_types)

    if playback_methods and len(playback_methods) > 0:
        placeholders = ",".join(["?" for _ in playback_methods])
        conditions.append(f"PlaybackMethod IN ({placeholders})")
        params.extend(playback_methods)

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params


@router.get("/top-content")
async def get_top_content(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    item_type: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取热门内容排行（剧集按剧名聚合，电影等按ItemId）"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None
    type_list = [item_type] if item_type else None

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
        query = f"""
            SELECT
                ItemId,
                ItemName,
                ItemType,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY ItemId
        """

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
            backdrop_url = emby_service.get_backdrop_url(str(item_id), item_type_val, item_info)

            # 获取 overview（剧集介绍）
            overview = item_info.get("Overview", "") if item_info else ""
            # 如果是单集，尝试获取剧集总介绍
            if item_type_val == "Episode" and item_info:
                series_id = item_info.get("SeriesId")
                if series_id:
                    series_info = await emby_service.get_item_info(series_id)
                    if series_info:
                        overview = series_info.get("Overview", overview)
                        # 也尝试从剧集获取 backdrop
                        if not backdrop_url and series_info.get("BackdropImageTags"):
                            backdrop_url = f"/api/backdrop/{series_id}"

            data.append({
                "item_id": item_id,
                "name": info["full_name"] or name,
                "show_name": name,
                "type": item_type_val,
                "play_count": info["play_count"],
                "duration_hours": round(info["duration"] / 3600, 2),
                "poster_url": poster_url,
                "backdrop_url": backdrop_url,
                "overview": overview
            })

    return {"top_content": data}


@router.get("/top-shows")
async def get_top_shows(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    users: Optional[str] = Query(default=None),
    clients: Optional[str] = Query(default=None),
    devices: Optional[str] = Query(default=None),
    playback_methods: Optional[str] = Query(default=None),
):
    """获取热门剧集（按剧名聚合）"""
    user_list = [u.strip() for u in users.split(",")] if users else None
    client_list = [c.strip() for c in clients.split(",")] if clients else None
    device_list = [d.strip() for d in devices.split(",")] if devices else None
    method_list = [m.strip() for m in playback_methods.split(",")] if playback_methods else None

    where_clause, params = build_filter_conditions(
        days=days if not (start_date or end_date) else None,
        start_date=start_date,
        end_date=end_date,
        users=user_list,
        clients=client_list,
        devices=device_list,
        item_types=["Episode"],  # 只查剧集
        playback_methods=method_list,
    )

    count_expr = get_count_expr()

    async with get_playback_db() as db:
        async with db.execute(f"""
            SELECT
                ItemId,
                ItemName,
                ItemType,
                {count_expr} as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE {where_clause}
            GROUP BY ItemId
        """, params) as cursor:
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
        backdrop_url = None
        overview = ""
        if data["item_id"]:
            info = await emby_service.get_item_info(str(data["item_id"]))
            if info and info.get("SeriesId"):
                series_id = info["SeriesId"]
                poster_url = f"/api/poster/{series_id}"
                # 获取剧集总介绍
                series_info = await emby_service.get_item_info(series_id)
                if series_info:
                    overview = series_info.get("Overview", "")
                    if series_info.get("BackdropImageTags"):
                        backdrop_url = f"/api/backdrop/{series_id}"

        result.append({
            "show_name": show_name,
            "play_count": data["play_count"],
            "duration_hours": round(data["duration"] / 3600, 2),
            "episode_count": len(data["episodes"]),
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
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


@router.get("/backdrop/{item_id}")
async def get_backdrop(
    item_id: str,
    maxHeight: int = Query(default=720),
    maxWidth: int = Query(default=1280)
):
    """代理获取 Emby 背景图(横版)"""
    content, content_type = await emby_service.get_backdrop(item_id, maxHeight, maxWidth)

    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"} if content else {}
    )


@router.get("/favorites")
async def get_favorites(
    days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    item_type: Optional[str] = Query(default=None),
):
    """获取用户收藏统计
    
    返回格式：
    - by_user: 按用户分组的收藏列表，每个用户包含其收藏的项目列表
    - ranking: 收藏次数最多的项目排行榜
    - stats: 统计信息（总收藏数、用户数、电影/剧集数）
    
    注意：此接口从 Emby API 获取收藏数据，不依赖数据库 IsFavorite 字段
    """
    try:
        # 从 Emby API 获取所有用户
        api_key = await emby_service.get_api_key()
        if not api_key:
            raise HTTPException(status_code=500, detail="无法获取 Emby API Key")
        
        async with httpx.AsyncClient() as client:
            # 获取所有用户列表
            users_resp = await client.get(
                f"{emby_service._emby_url}/emby/Users",
                params={"api_key": api_key},
                timeout=10
            )
            if users_resp.status_code != 200:
                raise HTTPException(status_code=500, detail="无法获取用户列表")
            
            users = users_resp.json()
            
            user_favorites_map = {}
            all_favorite_items = {}
            stats_movie_ids = set()
            stats_episode_ids = set()
            
            # 遍历每个用户，获取其收藏
            for user in users:
                user_id = user.get("Id")
                username = user.get("Name", "")
                
                # 获取用户的收藏项目
                favorites_resp = await client.get(
                    f"{emby_service._emby_url}/emby/Users/{user_id}/Items",
                    params={
                        "api_key": api_key,
                        "Filters": "IsFavorite",
                        "Recursive": "true",
                        "Fields": "Overview",
                        "IncludeItemTypes": item_type if item_type else "Movie,Series,Episode"
                    },
                    timeout=15
                )
                
                if favorites_resp.status_code == 200:
                    fav_data = favorites_resp.json()
                    items = fav_data.get("Items", [])
                    
                    if items:
                        user_fav_list = []
                        for item in items:
                            item_id = item.get("Id")
                            item_name = item.get("Name", "")
                            item_type_val = item.get("Type", "")
                            
                            # 应用类型筛选
                            if item_type and item_type_val != item_type:
                                continue
                            
                            user_fav_list.append({
                                "item_id": item_id,
                                "item_name": item_name,
                                "item_type": item_type_val,
                                "last_favorited": None
                            })
                            
                            # 统计全局收藏项
                            if item_id not in all_favorite_items:
                                all_favorite_items[item_id] = {
                                    "item_id": item_id,
                                    "item_name": item_name,
                                    "item_type": item_type_val,
                                    "favorite_count": 0
                                }
                            all_favorite_items[item_id]["favorite_count"] += 1
                            
                            # 统计电影/剧集数
                            if item_type_val == "Movie":
                                stats_movie_ids.add(item_id)
                            elif item_type_val == "Episode":
                                stats_episode_ids.add(item_id)
                        
                        if user_fav_list:
                            user_favorites_map[user_id] = {
                                "username": username,
                                "favorites": user_fav_list
                            }
            
            # 获取总用户数
            async with get_playback_db() as db:
                total_users_query = "SELECT COUNT(DISTINCT UserId) FROM PlaybackActivity WHERE UserId IS NOT NULL"
                async with db.execute(total_users_query) as cursor:
                    row = await cursor.fetchone()
                    total_users = row[0] if row else len(users)
            
            # 构建用户列表
            user_list = []
            for user_id, user_data in user_favorites_map.items():
                favorites = user_data["favorites"]
                movie_count = sum(1 for f in favorites if f["item_type"] == "Movie")
                episode_count = sum(1 for f in favorites if f["item_type"] == "Episode")
                
                user_list.append({
                    "user_id": user_id,
                    "username": user_data["username"],
                    "favorites": favorites,
                    "favorite_count": len(favorites),
                    "movie_count": movie_count,
                    "episode_count": episode_count
                })
            
            # 按收藏数量排序
            user_list.sort(key=lambda x: x["favorite_count"], reverse=True)
            
            # 构建排行榜
            ranking_list = sorted(all_favorite_items.values(), key=lambda x: x["favorite_count"], reverse=True)[:50]
            
            # 为每个项目获取海报信息
            for item in ranking_list:
                poster_info = await emby_service.get_item_images(item["item_id"])
                item["poster_url"] = poster_info.get("poster_url")
                item["backdrop_url"] = poster_info.get("backdrop_url")
                item["overview"] = poster_info.get("overview")
            
            for user in user_list:
                for fav in user["favorites"]:
                    poster_info = await emby_service.get_item_images(fav["item_id"])
                    fav["poster_url"] = poster_info.get("poster_url")
                    fav["backdrop_url"] = poster_info.get("backdrop_url")
                    fav["overview"] = poster_info.get("overview")
            
            # 计算统计信息
            stats = {
                "total_favorites": len(all_favorite_items),
                "total_users": total_users,
                "active_users": len(user_favorites_map),
                "movie_count": len(stats_movie_ids),
                "episode_count": len(stats_episode_ids)
            }
            
            return {
                "by_user": user_list,
                "ranking": ranking_list,
                "stats": stats
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取收藏数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取收藏数据失败: {str(e)}")
