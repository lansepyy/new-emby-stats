# Emby Stats - Webhook 通知功能集成说明

## ✅ 已集成的功能

### 后端功能

1. **配置存储系统** (`backend/config_storage.py`)
   - JSON配置文件存储于 `/data/webhook_config.json`
   - 支持动态加载和保存，无需重启服务

2. **Webhook服务** (`backend/services/`)
   - `webhook.py` - 事件处理和设备识别
   - `tmdb.py` - TMDB电影信息和图片获取
   - `notification.py` - 多平台通知发送（Telegram/企业微信/Discord）

3. **API路由**
   - `routers/webhook.py` - Webhook接收端点
   - `routers/config.py` - 配置管理API

4. **通知模板系统**
   - 支持5种事件模板（默认/播放/入库/登录/标记）
   - 使用Jinja2模板引擎
   - 可在Web界面自定义

### 前端功能

1. **通知配置页面** (`frontend/src/pages/Notifications.tsx`)
   - Telegram配置
   - 企业微信配置
   - Discord配置
   - TMDB配置
   - Webhook URL展示

2. **模板管理页面** (`frontend/src/pages/NotificationTemplates.tsx`)
   - 可视化模板编辑器
   - 变量参考文档
   - 实时保存

3. **UI集成**
   - 底部导航新增"通知"标签
   - 保持原有设计风格

## 📋 检查清单

### 后端文件
- [x] `backend/config.py` - 配置管理
- [x] `backend/config_storage.py` - 配置文件存储
- [x] `backend/requirements.txt` - Python依赖
- [x] `backend/routers/webhook.py` - Webhook路由
- [x] `backend/routers/config.py` - 配置API
- [x] `backend/services/webhook.py` - Webhook服务
- [x] `backend/services/tmdb.py` - TMDB服务
- [x] `backend/services/notification.py` - 通知服务

### 前端文件
- [x] `frontend/src/pages/Notifications.tsx` - 通知配置页
- [x] `frontend/src/pages/NotificationTemplates.tsx` - 模板管理页
- [x] `frontend/src/pages/index.ts` - 页面导出
- [x] `frontend/src/App.tsx` - 路由集成
- [x] `frontend/src/components/Layout.tsx` - 导航集成

### Docker文件
- [x] `Dockerfile` - 镜像构建文件
- [x] `docker-compose.yml` - 容器编排文件

## 🔧 依赖项

新增Python依赖：
```
requests==2.31.0
jinja2==3.1.2
pyyaml==6.0.1
```

## 🚀 使用方法

### 1. 配置Emby Webhook

在Emby服务器中配置Webhook插件：
- Webhook URL: `http://your-server:8899/api/webhook/emby`
- 选择要监听的事件（播放、入库、登录等）

### 2. Web界面配置

访问前端，进入"通知"页面：
1. 配置Telegram/企业微信/Discord参数
2. 配置TMDB API Key（可选）
3. 点击"保存配置"
4. 点击"测试通知"验证

### 3. 自定义模板

点击"模板管理"：
1. 选择要编辑的模板类型
2. 使用Jinja2语法自定义标题和内容
3. 参考可用变量列表
4. 保存模板

## 📦 Docker部署

### 构建镜像
```bash
docker build -t emby-stats .
```

### 使用docker-compose
```bash
docker-compose up -d
```

### 配置说明
- 配置文件自动保存在 `/data/webhook_config.json`
- 使用Docker卷持久化配置

## ⚠️ 注意事项

1. **数据目录**：配置文件保存在 `/data` 目录，需确保容器有写入权限
2. **端口映射**：默认8000端口，可在docker-compose.yml中修改
3. **实时生效**：所有配置修改后立即生效，无需重启服务
4. **权限问题**：确保Emby数据库目录正确挂载且可读

## 🐛 故障排查

### 配置无法保存
- 检查 `/data` 目录权限
- 查看容器日志: `docker logs emby-stats`

### 通知未发送
- 检查配置是否正确保存
- 点击"测试通知"验证配置
- 检查网络连接

### Webhook未触发
- 确认Emby Webhook插件已正确配置
- 检查URL是否可访问
- 查看后端日志

## 📝 配置文件示例

位置：`/data/webhook_config.json`

```json
{
  "telegram": {
    "bot_token": "your_bot_token",
    "admins": [123456789],
    "users": []
  },
  "wecom": {
    "corp_id": "",
    "secret": "",
    "agent_id": "",
    "proxy_url": "https://qyapi.weixin.qq.com",
    "to_user": "@all"
  },
  "discord": {
    "webhook_url": "",
    "username": "Emby通知",
    "avatar_url": ""
  },
  "tmdb": {
    "api_key": "",
    "image_base_url": "https://image.tmdb.org/t/p/original"
  },
  "templates": {
    "default": { ... },
    "playback": { ... },
    "library": { ... },
    "login": { ... },
    "mark": { ... }
  }
}
```

## ✨ 功能特性

- ✅ 多平台通知支持（Telegram/企业微信/Discord）
- ✅ TMDB图片和信息获取
- ✅ 自定义Jinja2通知模板
- ✅ 设备识别和IP信息
- ✅ 播放进度跟踪
- ✅ Web界面配置管理
- ✅ 实时配置生效
- ✅ 不影响原有功能
