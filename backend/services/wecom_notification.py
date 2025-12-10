"""
企业微信通知服务
提供企业微信消息发送功能
"""
import json
import aiohttp
import aiosqlite
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import settings
from database import get_playback_db, get_users_db


class WeComNotificationConfig:
    """企业微信通知配置"""
    def __init__(self, id: str, name: str, webhook_url: str, enabled: bool, created_at: str, updated_at: str):
        self.id = id
        self.name = name
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'webhook_url': self.webhook_url,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeComNotificationConfig':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            name=data['name'],
            webhook_url=data['webhook_url'],
            enabled=data['enabled'],
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )


class WeComNotificationService:
    """企业微信通知服务类"""
    
    def __init__(self):
        self.db_tables = {
            'configs': 'CREATE TABLE IF NOT EXISTS wecom_configs (id TEXT PRIMARY KEY, name TEXT NOT NULL, webhook_url TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)',
            'logs': 'CREATE TABLE IF NOT EXISTS wecom_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, config_id TEXT, template_id TEXT, message_content TEXT, status TEXT, error_message TEXT, sent_at TEXT NOT NULL, FOREIGN KEY (config_id) REFERENCES wecom_configs (id), FOREIGN KEY (template_id) REFERENCES notification_templates (id))'
        }
    
    async def init_tables(self):
        """初始化数据库表"""
        async with aiosqlite.connect(settings.USERS_DB) as db:
            await db.execute(self.db_tables['configs'])
            await db.execute(self.db_tables['logs'])
            await db.commit()
    
    async def get_all_configs(self) -> List[WeComNotificationConfig]:
        """获取所有企业微信配置"""
        await self.init_tables()
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM wecom_configs ORDER BY created_at DESC'
            )
            rows = await cursor.fetchall()
            
            configs = []
            for row in rows:
                config_data = dict(row)
                configs.append(WeComNotificationConfig.from_dict(config_data))
            
            return configs
    
    async def get_config_by_id(self, config_id: str) -> Optional[WeComNotificationConfig]:
        """根据ID获取企业微信配置"""
        configs = await self.get_all_configs()
        for config in configs:
            if config.id == config_id:
                return config
        return None
    
    async def get_enabled_configs(self) -> List[WeComNotificationConfig]:
        """获取启用的企业微信配置"""
        all_configs = await self.get_all_configs()
        return [c for c in all_configs if c.enabled]
    
    async def create_config(self, name: str, webhook_url: str, enabled: bool = True) -> WeComNotificationConfig:
        """创建企业微信配置"""
        import uuid
        from datetime import datetime
        
        await self.init_tables()
        
        config_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        config = WeComNotificationConfig(
            id=config_id,
            name=name,
            webhook_url=webhook_url,
            enabled=enabled,
            created_at=now,
            updated_at=now
        )
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            await db.execute(
                'INSERT INTO wecom_configs (id, name, webhook_url, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                (config_id, name, webhook_url, 1 if enabled else 0, now, now)
            )
            await db.commit()
        
        return config
    
    async def update_config(self, config_id: str, name: str, webhook_url: str, enabled: bool) -> bool:
        """更新企业微信配置"""
        from datetime import datetime
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            now = datetime.now().isoformat()
            cursor = await db.execute(
                'UPDATE wecom_configs SET name = ?, webhook_url = ?, enabled = ?, updated_at = ? WHERE id = ?',
                (name, webhook_url, 1 if enabled else 0, now, config_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def delete_config(self, config_id: str) -> bool:
        """删除企业微信配置"""
        async with aiosqlite.connect(settings.USERS_DB) as db:
            cursor = await db.execute('DELETE FROM wecom_configs WHERE id = ?', (config_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def send_message(self, config_id: str, content: str, template_id: Optional[str] = None) -> bool:
        """发送企业微信消息"""
        config = await self.get_config_by_id(config_id)
        if not config or not config.enabled:
            await self._log_notification(config_id, template_id, content, 'failed', '配置不存在或已禁用')
            return False
        
        try:
            success = await self._send_to_wecom(config.webhook_url, content)
            status = 'success' if success else 'failed'
            error_msg = None if success else '发送失败'
            
            await self._log_notification(config_id, template_id, content, status, error_msg)
            return success
            
        except Exception as e:
            await self._log_notification(config_id, template_id, content, 'failed', str(e))
            return False
    
    async def _send_to_wecom(self, webhook_url: str, content: str) -> bool:
        """发送到企业微信"""
        try:
            # 企业微信机器人消息格式
            message_data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=message_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('errcode', 0) == 0
                    return False
                    
        except Exception as e:
            print(f"企业微信消息发送失败: {e}")
            return False
    
    async def _log_notification(self, config_id: str, template_id: Optional[str], message_content: str, status: str, error_message: Optional[str] = None):
        """记录通知日志"""
        from datetime import datetime
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            await db.execute(
                'INSERT INTO wecom_logs (config_id, template_id, message_content, status, error_message, sent_at) VALUES (?, ?, ?, ?, ?, ?)',
                (config_id, template_id, message_content, status, error_message, datetime.now().isoformat())
            )
            await db.commit()
    
    async def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取通知日志"""
        await self.init_tables()
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                '''SELECT l.*, c.name as config_name, t.name as template_name 
                   FROM wecom_logs l 
                   LEFT JOIN wecom_configs c ON l.config_id = c.id 
                   LEFT JOIN notification_templates t ON l.template_id = t.id 
                   ORDER BY l.sent_at DESC LIMIT ?''', 
                (limit,)
            )
            rows = await cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    async def test_connection(self, webhook_url: str) -> Dict[str, Any]:
        """测试企业微信连接"""
        test_content = "🧪 这是一条测试消息，验证企业微信通知配置是否正确。\n\n如果收到此消息，说明配置成功！"
        
        try:
            success = await self._send_to_wecom(webhook_url, test_content)
            return {
                'success': success,
                'message': '连接测试成功' if success else '连接测试失败'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接测试出错: {str(e)}'
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取通知统计信息"""
        await self.init_tables()
        
        async with aiosqlite.connect(settings.USERS_DB) as db:
            db.row_factory = aiosqlite.Row
            
            # 总配置数
            cursor = await db.execute('SELECT COUNT(*) as count FROM wecom_configs')
            total_configs = (await cursor.fetchone())['count']
            
            # 启用配置数
            cursor = await db.execute('SELECT COUNT(*) as count FROM wecom_configs WHERE enabled = 1')
            enabled_configs = (await cursor.fetchone())['count']
            
            # 总发送次数
            cursor = await db.execute('SELECT COUNT(*) as count FROM wecom_logs')
            total_sent = (await cursor.fetchone())['count']
            
            # 成功发送次数
            cursor = await db.execute('SELECT COUNT(*) as count FROM wecom_logs WHERE status = "success"')
            success_sent = (await cursor.fetchone())['count']
            
            # 失败发送次数
            cursor = await db.execute('SELECT COUNT(*) as count FROM wecom_logs WHERE status = "failed"')
            failed_sent = (await cursor.fetchone())['count']
            
            # 成功率
            success_rate = (success_sent / total_sent * 100) if total_sent > 0 else 0
            
            return {
                'total_configs': total_configs,
                'enabled_configs': enabled_configs,
                'total_sent': total_sent,
                'success_sent': success_sent,
                'failed_sent': failed_sent,
                'success_rate': round(success_rate, 2)
            }


# 全局企业微信通知服务实例
wecom_notification_service = WeComNotificationService()