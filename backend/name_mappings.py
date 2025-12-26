"""
名称映射模块
支持客户端名称和设备名称的自定义映射
通过 JSON 配置文件进行配置
"""
import os
import json
from typing import Optional

# 映射配置文件路径（默认保存到 /config 目录，该目录可写）
MAPPINGS_FILE = os.getenv("NAME_MAPPINGS_FILE", "/config/name_mappings.json")

# 默认映射配置示例
DEFAULT_MAPPINGS = {
    "clients": {
        # 示例: "Emby Web": "Web",
        # "Emby for Android": "Android",
        # "Emby for iOS": "iOS",
    },
    "devices": {
        # 示例: "Mozilla Firefox Windows": "Firefox",
        # "Samsung UE55TU8000 Series (55)": "Samsung TV",
        # "iPhone 15 Pro Max": "iPhone",
    }
}


class NameMappingService:
    """名称映射服务"""

    def __init__(self):
        self._mappings: dict = {"clients": {}, "devices": {}}
        self._loaded = False

    def _load_mappings(self) -> None:
        """加载映射配置文件"""
        if self._loaded:
            return

        try:
            if os.path.exists(MAPPINGS_FILE):
                with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._mappings = {
                        "clients": data.get("clients", {}),
                        "devices": data.get("devices", {})
                    }
                    print(f"[NameMapping] 已加载映射配置: {len(self._mappings['clients'])} 个客户端, {len(self._mappings['devices'])} 个设备")
            else:
                print(f"[NameMapping] 配置文件不存在: {MAPPINGS_FILE}, 使用默认配置")
                self._mappings = DEFAULT_MAPPINGS.copy()
        except json.JSONDecodeError as e:
            print(f"[NameMapping] 配置文件解析失败: {e}, 使用默认配置")
            self._mappings = DEFAULT_MAPPINGS.copy()
        except Exception as e:
            print(f"[NameMapping] 加载配置失败: {e}, 使用默认配置")
            self._mappings = DEFAULT_MAPPINGS.copy()

        self._loaded = True

    def reload(self) -> None:
        """重新加载配置文件"""
        self._loaded = False
        self._load_mappings()

    def map_client_name(self, original: Optional[str]) -> str:
        """
        映射客户端名称
        如果存在映射则返回映射后的名称，否则返回原名称
        """
        self._load_mappings()
        if not original:
            return "Unknown"
        return self._mappings["clients"].get(original, original)

    def map_device_name(self, original: Optional[str]) -> str:
        """
        映射设备名称
        如果存在映射则返回映射后的名称，否则返回原名称
        """
        self._load_mappings()
        if not original:
            return "Unknown"
        return self._mappings["devices"].get(original, original)

    def get_all_mappings(self) -> dict:
        """获取所有映射配置"""
        self._load_mappings()
        return self._mappings.copy()

    def save_mappings(self, mappings: dict) -> bool:
        """保存映射配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(MAPPINGS_FILE), exist_ok=True)

            with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)

            # 更新内存中的配置
            self._mappings = {
                "clients": mappings.get("clients", {}),
                "devices": mappings.get("devices", {})
            }
            print(f"[NameMapping] 配置已保存: {MAPPINGS_FILE}")
            return True
        except Exception as e:
            print(f"[NameMapping] 保存配置失败: {e}")
            return False


# 单例实例
name_mapping_service = NameMappingService()
