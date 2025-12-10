"""
通知模板服务
提供通知模板的创建、管理和渲染功能
"""
import json
import aiosqlite
from typing import Dict, List, Any, Optional
from database import get_playback_db, get_users_db
from config import settings


class NotificationTemplate:
    """通知模板类"""
    def __init__(self, id: str, name: str, channel: str, template_content: str, variables: List[str], created_at: str, updated_at: str):
        self.id = id
        self.name = name
        self.channel = channel
        self.template_content = template_content
        self.variables = variables
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'channel': self.channel,
            'template_content': self.template_content,
            'variables': self.variables,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationTemplate':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            name=data['name'],
            channel=data['channel'],
            template_content=data['template_content'],
            variables=data.get('variables', []),
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )


class NotificationTemplateService:
    """通知模板服务类"""
    
    def __init__(self):
        self.db_tables = {
            'templates': 'CREATE TABLE IF NOT EXISTS notification_templates (id TEXT PRIMARY KEY, name TEXT NOT NULL, channel TEXT NOT NULL, template_content TEXT NOT NULL, variables TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)'
        }
    
    async def init_tables(self):
        """初始化数据库表"""
        async with aiosqlite.connect(settings.USERS_DB) as db:
            await db.execute(self.db_tables['templates'])
            await db.commit()
    
    async def get_all_templates(self) -> List[NotificationTemplate]:
        """获取所有通知模板"""
        await self.init_tables()
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM notification_templates ORDER BY created_at DESC'
            )
            rows = await cursor.fetchall()
            
            templates = []
            for row in rows:
                template_data = dict(row)
                template_data['variables'] = json.loads(template_data['variables'])
                templates.append(NotificationTemplate.from_dict(template_data))
            
            return templates
    
    async def get_template_by_channel(self, channel: str) -> List[NotificationTemplate]:
        """根据渠道获取通知模板"""
        all_templates = await self.get_all_templates()
        return [t for t in all_templates if t.channel == channel]
    
    async def get_template_by_id(self, template_id: str) -> Optional[NotificationTemplate]:
        """根据ID获取通知模板"""
        templates = await self.get_all_templates()
        for template in templates:
            if template.id == template_id:
                return template
        return None
    
    async def create_template(self, name: str, channel: str, template_content: str, variables: List[str]) -> NotificationTemplate:
        """创建通知模板"""
        import uuid
        from datetime import datetime
        
        await self.init_tables()
        
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        template = NotificationTemplate(
            id=template_id,
            name=name,
            channel=channel,
            template_content=template_content,
            variables=variables,
            created_at=now,
            updated_at=now
        )
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            await db.execute(
                'INSERT INTO notification_templates (id, name, channel, template_content, variables, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (template_id, name, channel, template_content, json.dumps(variables), now, now)
            )
            await db.commit()
        
        return template
    
    async def update_template(self, template_id: str, name: str, template_content: str, variables: List[str]) -> bool:
        """更新通知模板"""
        from datetime import datetime
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            now = datetime.now().isoformat()
            cursor = await db.execute(
                'UPDATE notification_templates SET name = ?, template_content = ?, variables = ?, updated_at = ? WHERE id = ?',
                (name, template_content, json.dumps(variables), now, template_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def delete_template(self, template_id: str) -> bool:
        """删除通知模板"""
        async with aiosqlite.connect(settings.USERS_DB) as db:
            cursor = await db.execute('DELETE FROM notification_templates WHERE id = ?', (template_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def render_template(self, template_id: str, context: Dict[str, Any]) -> str:
        """渲染通知模板"""
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError("模板不存在")
        
        content = template.template_content
        for var in template.variables:
            placeholder = f"{{{var}}}"
            if placeholder in content:
                value = context.get(var, f"{{{var}}}")
                content = content.replace(placeholder, str(value))
        
        return content
    
    def get_default_templates(self) -> List[Dict[str, Any]]:
        """获取默认模板"""
        return [
            {
                'name': '日常播放统计',
                'channel': 'wecom',
                'template_content': '📊 Emby 播放统计报告\n\n📅 统计时间: {date_range}\n🎬 总播放次数: {total_plays}\n⏱️ 总播放时长: {total_duration}\n👥 活跃用户: {active_users}\n🔥 最热内容: {top_content}\n\n📈 详细数据请查看 Emby Stats',
                'variables': ['date_range', 'total_plays', 'total_duration', 'active_users', 'top_content']
            },
            {
                'name': '用户活动提醒',
                'channel': 'wecom',
                'template_content': '👤 用户活动提醒\n\n👥 用户: {username}\n🎬 观看内容: {content_title}\n⏱️ 播放时长: {duration}\n📺 设备: {device}\n🕐 观看时间: {watch_time}\n\n🎯 继续享受观影体验！',
                'variables': ['username', 'content_title', 'duration', 'device', 'watch_time']
            },
            {
                'name': '新用户注册通知',
                'channel': 'wecom',
                'template_content': '🆕 新用户注册\n\n👤 用户名: {username}\n📧 邮箱: {email}\n📱 注册设备: {device}\n🕐 注册时间: {register_time}\n\n👋 欢迎新用户！',
                'variables': ['username', 'email', 'device', 'register_time']
            }
        ]
    
    async def create_default_templates(self):
        """创建默认模板"""
        existing_templates = await self.get_all_templates()
        if existing_templates:
            return  # 如果已有模板，不创建默认模板
        
        default_templates = self.get_default_templates()
        for template_data in default_templates:
            await self.create_template(
                name=template_data['name'],
                channel=template_data['channel'],
                template_content=template_data['template_content'],
                variables=template_data['variables']
            )


# 全局通知模板服务实例
notification_template_service = NotificationTemplateService()