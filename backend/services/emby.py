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
        self._emby_url = settings.EMBY_URL
        self._emby_url = settings.EMBY_URL

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

    async def get_user_info(self, user_id: str) -> dict:
        """获取用户信息"""
        try:
            api_key = await self.get_api_key()
            if not api_key:
                return {}

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/emby/Users/{user_id}",
                    params={"api_key": api_key},
                    timeout=10
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            print(f"Error getting user info for {user_id}: {e}")
        return {}

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
                        "Fields": "SeriesInfo,ImageTags,SeriesPrimaryImageTag,PrimaryImageAspectRatio,Overview,BackdropImageTags"
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

    async def get_backdrop(self, item_id: str, max_height: int = 720, max_width: int = 1280) -> tuple[bytes, str]:
        """获取背景图(横版)，返回 (图片数据, content_type)"""
        try:
            api_key = await self.get_api_key()
            if not api_key:
                return b"", "image/jpeg"

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/emby/Items/{item_id}/Images/Backdrop",
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
            print(f"Error fetching backdrop for {item_id}: {e}")

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

    async def upload_library_image(self, library_id: str, image_data: bytes, image_type: str = "Primary") -> bool:
        """
        上传图片到媒体库
        
        Args:
            library_id: 媒体库ID
            image_data: 图片数据
            image_type: 图片类型 (Primary/Backdrop/Logo等)
            
        Returns:
            上传是否成功
        """
        try:
            api_key = await self.get_api_key()
            if not api_key:
                print("未找到API密钥")
                return False
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 检测图片格式
                content_type = "image/png"
                if image_data[:4] == b'\x89PNG':
                    content_type = "image/png"
                elif image_data[:2] == b'\xff\xd8':
                    content_type = "image/jpeg"
                elif image_data[:6] in (b'GIF87a', b'GIF89a'):
                    content_type = "image/gif"
                elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
                    content_type = "image/webp"
                
                # Emby API: POST /Items/{Id}/Images/{Type}
                response = await client.post(
                    f"{settings.EMBY_URL}/emby/Items/{library_id}/Images/{image_type}",
                    params={"api_key": api_key},
                    content=image_data,
                    headers={
                        "Content-Type": content_type
                    }
                )
                
                if response.status_code in [200, 204]:
                    print(f"成功上传封面到媒体库 {library_id}")
                    return True
                else:
                    print(f"上传封面失败: {response.status_code}, {response.text}")
                    return False
                    
        except Exception as e:
            print(f"上传封面异常: {e}")
            return False
    
    def get_backdrop_url(self, item_id: str, item_type: str, item_info: dict) -> str | None:
        """根据媒体信息获取背景图(横版) URL"""
        if not item_info:
            return None

        # 对于剧集，使用剧集背景图
        if item_type == "Episode" and item_info.get("SeriesId"):
            return f"/api/backdrop/{item_info['SeriesId']}"
        # 检查是否有 Backdrop 图片
        elif item_info.get("BackdropImageTags") and len(item_info.get("BackdropImageTags", [])) > 0:
            return f"/api/backdrop/{item_id}"

        return None

    async def get_item_images(self, item_id: str) -> dict:
        """获取项目的图片URL和概述信息"""
        try:
            item_info = await self.get_item_info(item_id)
            if not item_info:
                return {}
            
            item_type = item_info.get("Type", "")
            
            return {
                "poster_url": self.get_poster_url(item_id, item_type, item_info),
                "backdrop_url": self.get_backdrop_url(item_id, item_type, item_info),
                "overview": item_info.get("Overview", "")
            }
        except Exception as e:
            print(f"Error getting item images for {item_id}: {e}")
            return {}

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
