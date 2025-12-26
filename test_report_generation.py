"""
测试报告图片生成
用于测试新的竖版报告生成效果
"""
import sys
import os
from pathlib import Path

# 添加后端目录到路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.report_image import ReportImageService

# 测试数据
test_report = {
    "title": "Emby 观影周报",
    "period": "2025-12-09 至 2025-12-15",
    "summary": {
        "total_plays": 127,
        "total_hours": 45.5,
    },
    "top_content": [
        {
            "name": "流浪地球2",
            "type": "Movie",
            "play_count": 15,
            "hours": 5.2,
            "item_id": "1"
        },
        {
            "name": "三体 - 第1集",
            "type": "Episode",
            "play_count": 12,
            "hours": 4.8,
            "item_id": "2"
        },
        {
            "name": "长津湖之水门桥",
            "type": "Movie",
            "play_count": 10,
            "hours": 4.1,
            "item_id": "3"
        },
        {
            "name": "觉醒年代 - 第5集",
            "type": "Episode",
            "play_count": 8,
            "hours": 3.5,
            "item_id": "4"
        },
        {
            "name": "我和我的祖国",
            "type": "Movie",
            "play_count": 6,
            "hours": 2.9,
            "item_id": "5"
        }
    ]
}

def main():
    print("测试报告图片生成...")
    print(f"测试数据: {test_report['title']}")
    
    # 创建服务
    service = ReportImageService()
    
    # 生成图片（不带封面图）
    print("\n生成报告图片（无封面）...")
    image_bytes = service.generate_report_image(test_report)
    
    # 保存到文件
    output_path = Path(__file__).parent.parent / "test_report.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    
    print(f"✅ 报告图片已生成: {output_path}")
    print(f"📦 文件大小: {len(image_bytes) / 1024:.2f} KB")
    print(f"📐 图片宽度: {service.width}px")
    
    # 检查资源目录
    res_dir = service.res_dir
    print(f"\n📂 资源目录: {res_dir}")
    print(f"   - 是否存在: {'✅' if res_dir.exists() else '❌'}")
    
    bg_dir = res_dir / "bg"
    if bg_dir.exists():
        bg_files = list(bg_dir.glob("*.jpg")) + list(bg_dir.glob("*.png"))
        print(f"   - 背景图片: {len(bg_files)} 张")
        for bg in bg_files:
            print(f"     • {bg.name}")
    else:
        print(f"   - 背景图片: 无 (使用纯色背景)")
    
    font_files = list(res_dir.glob("*.ttf")) + list(res_dir.glob("*.ttc"))
    if font_files:
        print(f"   - 字体文件: {len(font_files)} 个")
        for font in font_files:
            print(f"     • {font.name}")
    else:
        print(f"   - 字体文件: 无 (使用系统字体)")
    
    print("\n💡 提示:")
    print("   1. 将 MP 插件的背景图片复制到 res/bg/ 目录")
    print("   2. 将字体文件复制到 res/ 目录")
    print("   3. 重新运行此脚本查看效果")

if __name__ == "__main__":
    main()
