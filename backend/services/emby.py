"""
Emby API 服务模块
处理与 Emby 服务器的所有交互
"""
import httpx
import aiosqlite
from config import settings


class EmbyService:
    """Emby 服务类，管理与 Emby 服务器的交互"""

    def __init__(self):
        self._api_key_cache: str | None = None
        self._user_id_cache: str | None = None
        self._item_info_cache: dict = {}

    async def get_api_key(self) -> str:
        """获取 Emby API Key，优先使用环境变量，否则从数据库获取"""
        # 优先使用环境变量配置的 API Key
        if settings.EMBY_API_KEY:
            return settings.EMBY_API_KEY

        if self._api_key_cache:
            return self._api_key_cache

        try:
            async with aiosqlite.connect(settings.AUTH_DB) as db:
                async with db.execute(
                    "SELECT AccessToken FROM Tokens_2 WHERE IsActive=1 ORDER BY DateLastActivityInt DESC LIMIT 1"
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        self._api_key_cache = row[0]
                        return self._api_key_cache
        except Exception as e:
            print(f"Error getting API key: {e}")
        return ""

    async def get_user_id(self) -> str:
        """获取一个 Emby 用户 ID 用于 API 调用"""
        if self._user_id_cache:
            return self._user_id_cache

        try:
            api_key = await self.get_api_key()
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/emby/Users",
                    params={"api_key": api_key},
                    timeout=10
                )
                if resp.status_code == 200:
                    users = resp.json()
                    if users:
                        self._user_id_cache = users[0]["Id"]
                        return self._user_id_cache
        except Exception as e:
            print(f"Error getting user ID: {e}")
        return ""

    async def get_item_info(self, item_id: str) -> dict:
        """获取媒体项目信息（包含海报等）"""
        if item_id in self._item_info_cache:
            return self._item_info_cache[item_id]

        try:
            api_key = await self.get_api_key()
            user_id = await self.get_user_id()
            if not api_key or not user_id:
                return {}

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/emby/Users/{user_id}/Items/{item_id}",
                    params={
                        "api_key": api_key,
                        "Fields": "SeriesInfo,ImageTags,SeriesPrimaryImageTag,PrimaryImageAspectRatio,Overview"
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    info = resp.json()
                    self._item_info_cache[item_id] = info
                    # 限制缓存大小
                    if len(self._item_info_cache) > settings.ITEM_CACHE_MAX_SIZE:
                        keys = list(self._item_info_cache.keys())[:settings.ITEM_CACHE_EVICT_COUNT]
                        for k in keys:
                            del self._item_info_cache[k]
                    return info
        except Exception as e:
            print(f"Error getting item info for {item_id}: {e}")
        return {}

    async def get_poster(self, item_id: str, max_height: int = 300, max_width: int = 200) -> tuple[bytes, str]:
        """获取海报图片，返回 (图片数据, content_type)"""
        try:
            api_key = await self.get_api_key()
            if not api_key:
                return b"", "image/jpeg"

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/emby/Items/{item_id}/Images/Primary",
                    params={
                        "api_key": api_key,
                        "maxHeight": max_height,
                        "maxWidth": max_width,
                        "quality": 90
                    },
                    timeout=15
                )
                if resp.status_code == 200:
                    return resp.content, resp.headers.get("content-type", "image/jpeg")
        except Exception as e:
            print(f"Error fetching poster for {item_id}: {e}")

        return b"", "image/jpeg"

    def get_poster_url(self, item_id: str, item_type: str, item_info: dict) -> str | None:
        """根据媒体信息获取海报 URL"""
        if not item_info:
            return None

        # 对于剧集，使用剧集海报；对于电影，使用自身海报
        if item_type == "Episode" and item_info.get("SeriesId"):
            return f"/api/poster/{item_info['SeriesId']}"
        elif item_info.get("ImageTags", {}).get("Primary"):
            return f"/api/poster/{item_id}"

        return None

    async def get_now_playing(self) -> list[dict]:
        """获取当前正在播放的会话"""
        try:
            api_key = await self.get_api_key()
            if not api_key:
                return []

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/emby/Sessions",
                    params={"api_key": api_key},
                    timeout=10
                )
                if resp.status_code == 200:
                    sessions = resp.json()
                    playing = []
                    for session in sessions:
                        # 只返回正在播放的会话
                        if session.get("NowPlayingItem"):
                            playing.append(session)
                    return playing
        except Exception as e:
            print(f"Error getting now playing: {e}")
        return []

    async def authenticate_user(self, username: str, password: str) -> dict | None:
        """
        使用 Emby API 验证用户登录
        返回用户信息 dict 或 None（验证失败）
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.EMBY_URL}/emby/Users/AuthenticateByName",
                    headers={
                        "X-Emby-Authorization": 'MediaBrowser Client="Emby Stats", Device="Web", DeviceId="emby-stats", Version="1.0.0"',
                        "Content-Type": "application/json"
                    },
                    json={
                        "Username": username,
                        "Pw": password
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "user_id": data.get("User", {}).get("Id"),
                        "username": data.get("User", {}).get("Name"),
                        "access_token": data.get("AccessToken"),
                        "is_admin": data.get("User", {}).get("Policy", {}).get("IsAdministrator", False)
                    }
        except Exception as e:
            print(f"Error authenticating user: {e}")
        return None


# 单例实例
emby_service = EmbyService()
