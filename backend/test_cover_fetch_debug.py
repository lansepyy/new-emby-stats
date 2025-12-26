"""
调试封面获取问题
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.report_image import ReportImageService
from services.report import report_service
from config_storage import config_storage

async def test_cover_fetch():
    """测试封面获取完整流程"""
    print("=" * 50)
    print("1. 检查配置")
    print("=" * 50)
    
    # 检查服务器配置
    servers = config_storage.get("servers", {})
    print(f"Servers 配置: {servers}")
    
    if servers:
        server_id = list(servers.keys())[0]
        server = servers[server_id]
        print(f"服务器 URL: {server.get('url')}")
        print(f"API Key: {server.get('api_key')[:10]}..." if server.get('api_key') else "未配置")
    else:
        print("❌ 未找到服务器配置！")
        return
    
    print("\n" + "=" * 50)
    print("2. 初始化 ReportImageService")
    print("=" * 50)
    
    service = ReportImageService()
    print(f"服务 Emby URL: {service.emby_url}")
    print(f"服务 API Key: {'已配置' if service.emby_api_key else '未配置'}")
    
    print("\n" + "=" * 50)
    print("3. 生成报告数据")
    print("=" * 50)
    
    report = await report_service.generate_daily_report()
    print(f"报告标题: {report.get('title')}")
    print(f"报告周期: {report.get('period')}")
    
    top_content = report.get('top_content', [])
    print(f"\n热门内容数量: {len(top_content)}")
    
    for idx, item in enumerate(top_content[:3]):
        print(f"\n  #{idx+1}:")
        print(f"    名称: {item.get('name')}")
        print(f"    类型: {item.get('type')}")
        print(f"    Item ID: {item.get('item_id')}")
    
    print("\n" + "=" * 50)
    print("4. 测试封面获取")
    print("=" * 50)
    
    if top_content:
        test_item = top_content[0]
        item_id = test_item.get('item_id')
        item_name = test_item.get('name')
        
        print(f"\n测试项目: {item_name}")
        print(f"Item ID: {item_id}")
        
        if item_id:
            cover_bytes = service._fetch_cover_image(item_id)
            if cover_bytes:
                print(f"✅ 封面获取成功！大小: {len(cover_bytes)} bytes")
            else:
                print(f"❌ 封面获取失败！")
        else:
            print(f"❌ Item ID 为空！")
    else:
        print("❌ 没有热门内容数据")

if __name__ == "__main__":
    asyncio.run(test_cover_fetch())
