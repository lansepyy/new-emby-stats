"""
初始化通知模板功能
创建默认数据库表和模板
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置数据库路径到当前目录
os.environ["USERS_DB"] = os.path.join(os.getcwd(), "users.db")
os.environ["AUTH_DB"] = os.path.join(os.getcwd(), "auth.db")
os.environ["PLAYBACK_DB"] = os.path.join(os.getcwd(), "playback.db")

from services.notification_templates import notification_template_service
from services.wecom_notification import wecom_notification_service


async def init_notification_system():
    """初始化通知系统"""
    print("🚀 开始初始化通知模板系统...")
    print(f"📁 数据库路径: {os.getcwd()}")
    
    try:
        # 1. 创建数据库表
        print("📊 创建数据库表...")
        await notification_template_service.init_tables()
        await wecom_notification_service.init_tables()
        print("✅ 数据库表创建完成")
        
        # 2. 创建默认通知模板
        print("📝 创建默认通知模板...")
        await notification_template_service.create_default_templates()
        print("✅ 默认模板创建完成")
        
        print("🎉 通知模板系统初始化完成！")
        print("\n💡 功能说明:")
        print("- 通知模板: 支持创建和管理自定义模板")
        print("- 企业微信: 支持配置多个企业微信机器人")
        print("- 消息发送: 支持模板渲染和实时预览")
        print("- 统计分析: 提供发送成功率和日志统计")
        print("\n🔗 API端点:")
        print("- 模板管理: /api/notification-templates/*")
        print("- 企业微信: /api/wecom/*")
        print("\n🌐 前端访问:")
        print("- 点击顶部菜单的铃铛图标进入通知模板管理")
        print("- 在导航栏的'通知'标签页查看统计和日志")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(init_notification_system())