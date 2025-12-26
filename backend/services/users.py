"""
用户服务模块
处理用户相关的数据获取和匹配
"""
import json
import aiosqlite
from config import settings
from database import convert_guid_bytes_to_standard


class UserService:
    """用户服务类"""

    async def get_user_map(self) -> dict[str, str]:
        """获取用户ID到用户名的映射"""
        user_map = {}
        try:
            async with aiosqlite.connect(settings.USERS_DB) as db:
                async with db.execute("SELECT guid, data FROM LocalUsersv2") as cursor:
                    async for row in cursor:
                        guid_bytes = row[0]
                        data_bytes = row[1]
                        try:
                            # guid 是二进制格式，需要转换字节序
                            if isinstance(guid_bytes, bytes):
                                guid = convert_guid_bytes_to_standard(guid_bytes)
                            else:
                                guid = str(guid_bytes).lower().replace("-", "")
                            # data 是 JSON
                            if isinstance(data_bytes, bytes):
                                data = json.loads(data_bytes.decode('utf-8', errors='ignore'))
                            else:
                                data = json.loads(data_bytes)
                            user_map[guid] = data.get("Name", "Unknown")
                        except:
                            continue
        except Exception as e:
            print(f"Error loading users: {e}")
        return user_map

    def match_username(self, user_id: str, user_map: dict[str, str]) -> str:
        """根据用户ID匹配用户名"""
        if not user_id:
            return "Unknown"

        # 直接匹配
        username = user_map.get(user_id)
        if username:
            return username

        # 尝试不同格式匹配
        user_id_normalized = user_id.replace("-", "").lower()
        for uid, name in user_map.items():
            if user_id_normalized in uid.lower() or uid.lower() in user_id_normalized:
                return name

        # 无法匹配，返回截断的ID
        return user_id[:8] + "..." if len(user_id) > 8 else user_id


# 单例实例
user_service = UserService()
