# 通知设置功能文档

本文档描述了 Emby Stats 项目中新添加的通知设置功能和 API 端点。

## 功能概述

通知设置功能允许用户通过 Web 界面配置和管理各种通知渠道，包括 Telegram、Discord、企业微信等，以及自定义通知模板。

## 核心组件

### 1. 通知设置存储 (`backend/notification_settings.py`)

集中管理所有通知配置的存储服务，包含以下特性：

- **文件持久化**：配置保存在 `/config/notification_settings.json`
- **环境变量可覆盖**：可通过 `NOTIFICATION_SETTINGS_FILE` 环境变量指定配置文件路径
- **线程安全**：使用锁机制确保并发访问安全
- **配置验证**：使用 Pydantic 模型进行数据验证
- **变更回调**：支持注册回调函数以响应配置变更

#### 支持的配置项

- **基础设置**
  - `enabled`: 通知功能总开关
  - `debug`: 调试模式开关
  
- **Emby 连接配置**
  - `url`: Emby 服务器地址
  - `api_key`: Emby API 密钥

- **Telegram 配置**
  - `telegram_enabled`: Telegram 通知开关
  - `telegram_bot_token`: Bot Token
  - `telegram_admins`: 管理员列表
  - `telegram_users`: 用户列表

- **Discord 配置**
  - `discord_enabled`: Discord 通知开关
  - `discord_webhooks`: Webhook URL 列表（自动验证格式）

- **企业微信配置**
  - `wecom_enabled`: WeCom 通知开关
  - `wecom_config`: 企业微信详细配置（corp_id、secret、agent_id 等）

- **TMDB 配置**
  - `tmdb_enabled`: TMDB 功能开关
  - `tmdb_config`: TMDB API 配置

- **通知模板**
  - 5 个预设模板：default、playback、login、mark、library
  - 每个模板包含：title、text、image_template
  - 支持 Jinja2 风格的占位符：`{{ user_name }}`、`{{ item_name }}` 等

### 2. 通知 API 路由 (`backend/routers/notifications.py`)

提供完整的 RESTful API 来管理通知设置和模板。

## API 端点

### 设置管理

#### GET `/api/notifications/settings`
获取当前通知设置配置。

**响应示例：**
```json
{
  "success": true,
  "data": {
    "enabled": false,
    "debug": false,
    "emby_connection": {
      "url": "http://localhost:8096",
      "api_key": null
    },
    "telegram_enabled": false,
    "telegram_bot_token": null,
    "discord_enabled": false,
    "discord_webhooks": [],
    "templates": { ... },
    "effective_webhook_urls": []
  }
}
```

#### PUT `/api/notifications/settings`
更新通知设置配置。

**请求体：**
```json
{
  "enabled": true,
  "telegram_enabled": true,
  "telegram_bot_token": "123456789:ABC...",
  "discord_enabled": true
}
```

**响应示例：**
```json
{
  "success": true,
  "data": { ...current settings... },
  "message": "设置已更新"
}
```

### 模板管理

#### GET `/api/notifications/templates`
获取所有通知模板。

**响应示例：**
```json
{
  "success": true,
  "data": {
    "default": {
      "title": "Emby Stats 通知",
      "text": "这是一条来自 Emby Stats 的通知",
      "image_template": null
    },
    "playback": {
      "title": "播放开始通知",
      "text": "用户 {{ user_name }} 开始播放 {{ item_name }}",
      "image_template": "{{ item_image }}"
    }
  }
}
```

#### PUT `/api/notifications/templates/{template_id}`
更新指定模板。

**路径参数：**
- `template_id`: 模板ID，可选值：`default`、`playback`、`login`、`mark`、`library`

**请求体：**
```json
{
  "title": "自定义标题",
  "text": "自定义内容：{{ user_name }} 播放了 {{ item_name }}",
  "image_template": "https://example.com/image.jpg"
}
```

**限制：**
- 标题最多 200 字符
- 内容最多 2000 字符
- 自动去除首尾空格

#### POST `/api/notifications/templates/preview`
预览模板渲染结果。

**请求体：**
```json
{
  "template_id": "playback",
  "content": {
    "user_name": "张三",
    "item_name": "《流浪地球》",
    "item_image": "https://example.com/poster.jpg"
  }
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "template_id": "playback",
    "original_title": "播放开始通知",
    "original_text": "用户 {{ user_name }} 开始播放 {{ item_name }}",
    "original_image": "{{ item_image }}",
    "rendered_title": "播放开始通知",
    "rendered_text": "用户 张三 开始播放 《流浪地球》",
    "rendered_image": "https://example.com/poster.jpg",
    "sample_data": {
      "user_name": "张三",
      "item_name": "《流浪地球》"
    }
  }
}
```

## 配置持久化

### 配置文件位置

- **默认路径**: `/config/notification_settings.json`
- **可配置路径**: 通过环境变量 `NOTIFICATION_SETTINGS_FILE` 指定

### 配置文件格式

```json
{
  "enabled": false,
  "debug": false,
  "emby_connection": {
    "url": "http://localhost:8096",
    "api_key": null
  },
  "telegram_enabled": false,
  "telegram_bot_token": null,
  "telegram_admins": [],
  "telegram_users": [],
  "discord_enabled": false,
  "discord_webhooks": [],
  "wecom_enabled": false,
  "wecom_config": {
    "corp_id": "",
    "corp_secret": "",
    "agent_id": "",
    "proxy": null,
    "to_user": null
  },
  "tmdb_enabled": false,
  "tmdb_config": {
    "api_key": ""
  },
  "templates": {
    "default": {
      "title": "Emby Stats 通知",
      "text": "这是一条来自 Emby Stats 的通知",
      "image_template": null
    },
    "playback": {
      "title": "播放开始通知",
      "text": "用户 {{ user_name }} 开始播放 {{ item_name }}",
      "image_template": "{{ item_image }}"
    },
    "login": {
      "title": "登录通知",
      "text": "用户 {{ user_name }} 登录了系统",
      "image_template": null
    },
    "mark": {
      "title": "标记完成通知",
      "text": "{{ user_name }} 完成了对 {{ item_name }} 的标记",
      "image_template": "{{ item_image }}"
    },
    "library": {
      "title": "媒体库更新通知",
      "text": "媒体库已更新，新增 {{ item_count }} 个项目",
      "image_template": null
    }
  }
}
```

## 集成说明

### 1. 与配置模块集成

通知设置存储已集成到 `backend/config.py` 中：

```python
from notification_settings import notification_settings_store

class Settings:
    # ... 其他配置 ...
    
    # 通知设置存储实例
    notification_settings = notification_settings_store

settings = Settings()
```

### 2. 与主应用集成

通知路由已注册到主应用中：

```python
# 在 main.py 中
from routers import notifications_router

app.include_router(notifications_router)
```

### 3. 环境变量配置

```bash
# 通知配置文件路径（可选）
export NOTIFICATION_SETTINGS_FILE="/custom/path/notification_settings.json"
```

## 使用示例

### 1. 启用 Telegram 通知

```bash
curl -X PUT "http://localhost:8000/api/notifications/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "telegram_enabled": true,
    "telegram_bot_token": "123456789:ABC..."
  }'
```

### 2. 更新播放模板

```bash
curl -X PUT "http://localhost:8000/api/notifications/templates/playback" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "🎬 正在播放",
    "text": "{{ user_name }} 正在观看 {{ item_name }}",
    "image_template": "{{ item_poster }}"
  }'
```

### 3. 预览模板渲染

```bash
curl -X POST "http://localhost:8000/api/notifications/templates/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "playback",
    "content": {
      "user_name": "Alice",
      "item_name": "《阿凡达》",
      "item_poster": "https://example.com/avatar.jpg"
    }
  }'
```

## 错误处理

### 常见错误码

- `400 Bad Request`: 请求参数验证失败
  - 无效的模板ID
  - 内容长度超过限制
  - Discord Webhook URL 格式不正确

- `404 Not Found`: 模板不存在

- `500 Internal Server Error`: 服务器内部错误

### 错误响应示例

```json
{
  "detail": "无效的模板ID。可用选项: default, playback, login, mark, library"
}
```

## 最佳实践

1. **配置备份**: 定期备份 `/config/notification_settings.json` 文件
2. **敏感信息**: 避免在 Git 等版本控制系统提交包含真实 Token 的配置文件
3. **模板测试**: 使用预览功能测试模板变量替换是否正确
4. **错误监控**: 启用调试模式以获取详细的错误信息
5. **权限控制**: 确保只有授权用户能访问通知设置 API

## 后续开发

- **模板引擎升级**: 考虑集成更强大的 Jinja2 模板引擎
- **批量操作**: 支持批量更新多个模板
- **模板版本控制**: 保留模板历史版本
- **第三方集成**: 与实际的通知服务（Telegram Bot、Discord Webhook 等）集成
- **通知触发器**: 配置何时发送通知的条件

---

此功能为 Emby Stats 项目提供了完整的通知配置管理能力，支持多种通知渠道和自定义模板，满足不同用户的通知需求。