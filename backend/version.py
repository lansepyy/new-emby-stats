"""版本信息"""

VERSION = "2.2"

CHANGELOG = {
    "2.2": [
        "✨ 新增多服务器切换功能，支持管理和切换多个 Emby 服务器",
        "🔄 选择不同服务器时自动切换数据显示",
        "⚙️ 简化服务器管理表单，数据库路径配置可选",
    ],
    "2.1": [
        "🎨 优化版本弹窗背景，改为纯白色提高可读性",
        "📝 TMDB 配置添加详细图片 URL 格式说明",
        "💡 界面细节优化和用户体验提升",
    ],
    "2.0": [
        "✨ 集成 OneBot（QQ机器人）到所有通知场景",
        "✨ 支持定时报告推送到 QQ 群和私聊",
        "✨ 支持 Emby 实时事件推送到 QQ（播放/入库/登录/收藏）",
        "✨ 新增代理配置，解决 TMDB 访问问题",
        "✨ 新增版本信息显示和更新日志",
        "🎨 优化 TMDB 图片 URL 配置说明",
        "📝 完善文档说明",
    ],
    "1.0": [
        "🎉 初始版本发布",
        "📊 支持观影数据统计和报告",
        "📱 支持 Telegram/企业微信/Discord 通知",
        "🔔 支持 Emby Webhook 实时通知",
    ]
}


def get_version_info():
    """获取版本信息"""
    return {
        "version": VERSION,
        "changelog": CHANGELOG,
        "latest_changes": CHANGELOG.get(VERSION, [])
    }
