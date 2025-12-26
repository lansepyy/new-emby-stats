"""
测试实时获取封面图功能
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.report_image import ReportImageService
from config_storage import config_storage

def test_cover_fetch():
    """测试封面获取"""
    # 创建服务实例
    service = ReportImageService()
    
    print(f"Emby URL: {service.emby_url}")
    print(f"API Key: {'已配置' if service.emby_api_key else '未配置'}")
    
    # 测试获取封面（需要一个真实的 item_id）
    # 这里只是测试方法是否正常工作，不会真正下载
    test_item_id = "test123"
    result = service._fetch_cover_image(test_item_id)
    print(f"测试获取封面（item_id={test_item_id}）: {'成功' if result else '失败'}")

if __name__ == "__main__":
    test_cover_fetch()
