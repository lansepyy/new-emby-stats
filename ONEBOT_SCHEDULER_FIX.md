# OneBot 完整对接修复

## 问题描述

OneBot（QQ机器人）只能手动发送报告消息，存在以下两个问题：
1. **定时报告推送**：定时任务中没有对接 OneBot
2. **Emby Webhook 通知**：实时通知（播放、入库、登录、收藏等）也没有对接 OneBot

## 原因分析

代码中 OneBot 的功能实现分为三部分：

1. ✅ **配置管理** (`backend/routers/config.py`)
   - `OneBotConfig` 配置模型定义完整
   - 包含 `http_url`、`access_token`、`group_ids`、`user_ids` 等字段

2. ✅ **通知服务** (`backend/services/notification.py`)
   - `send_onebot()` - 发送文本和图片URL
   - `_send_onebot_photo_bytes()` - 发送图片字节数据（base64编码）
   - 支持发送到QQ群和私聊

3. ✅ **手动发送** (`backend/routers/report.py`)
   - `/api/report/send-image` 接口支持 OneBot
   - 可以手动触发报告发送

4. ❌ **定时任务** (`backend/services/scheduler.py`)
   - `_send_report()` 方法中**缺少 OneBot 的调用**
   - 只处理了 Telegram、企业微信、Discord 三个渠道
   - `_send_text_report()` 备用方案中也缺少 OneBot

5. ❌ **Webhook 实时通知** (`backend/routers/webhook.py`)
   - `handle_emby_webhook()` 处理器中**缺少 OneBot 配置**
   - `test_notification()` 测试接口中也缺少 OneBot
   - 导致播放、入库、登录、收藏等事件无法推送到 QQ

## 修复内容

### 1. 定时报告推送 (`backend/services/scheduler.py`)

#### 1. 获取 OneBot 配置

在 `_send_report()` 方法中添加 OneBot 配置读取：

```python
async def _send_report(self, report: dict):
    # 获取通知配置
    tg_config = config_storage.get_telegram_config()
    wecom_config = config_storage.get_wecom_config()
    discord_config = config_storage.get_discord_config()
    onebot_config = config_storage.get("onebot", {})  # ← 新增
```

#### 2. 添加到通知配置

将 OneBot 配置传递给通知服务：

```python
notification_config = {
    "telegram": {...},
    "wecom": wecom_config,
    "discord": discord_config,
    "onebot": onebot_config  # ← 新增
}
```

#### 3. 发送图片报告

在图片发送部分添加 OneBot 处理：

```python
# OneBot
if channels.get("onebot") and onebot_config.get("http_url"):
    try:
        if notification_service._send_onebot_photo_bytes(image_bytes, report_title):
            sent_count += 1
            logger.info("报告图片已通过 OneBot 发送")
    except Exception as e:
        logger.error(f"OneBot 发送失败: {e}")
```

#### 4. 文本报告备用方案

在 `_send_text_report()` 方法中也添加 OneBot 支持：

```python
async def _send_text_report(self, report: dict, tg_config: dict, wecom_config: dict, discord_config: dict, channels: dict):
    # 获取onebot配置
    onebot_config = config_storage.get("onebot", {})  # ← 新增
    
    notification_config = {
        "telegram": {...},
        "wecom": wecom_config,
        "discord": discord_config,
        "onebot": onebot_config  # ← 新增
    }
    
    # ... 其他渠道发送 ...
    
    # ← 新增 OneBot 文本发送
    if channels.get("onebot") and onebot_config.get("http_url"):
        try:
            await notification_service.send_onebot(report_title, report_text)
            logger.info("报告文本已通过 OneBot 发送")
        except Exception as e:
            logger.error(f"OneBot 发送失败: {e}")
```

### 2. Emby Webhook 实时通知 (`backend/routers/webhook.py`)

Emby Webhook 通知包括：
- 📺 **播放事件**：开始、暂停、继续、停止
- 📚 **入库事件**：新增电影、剧集
- 🔐 **登录事件**：成功、失败
- ⭐ **标记事件**：收藏、评分、已观看/未观看

#### 修复 1：Webhook 处理器

在 `handle_emby_webhook()` 函数中添加 OneBot 配置：

```python
@router.post("/emby")
async def handle_emby_webhook(request: Request):
    # 从配置文件获取通知配置
    tg_config = config_storage.get_telegram_config()
    wecom_config = config_storage.get_wecom_config()
    discord_config = config_storage.get_discord_config()
    onebot_config = config_storage.get("onebot", {})  # ← 新增
    tmdb_config = config_storage.get_tmdb_config()
    
    notification_config = {
        "telegram": {...},
        "wecom": wecom_config,
        "discord": discord_config,
        "onebot": onebot_config  # ← 新增
    }
    
    # ... 通过 notification_service.send_all() 发送到所有渠道
```

#### 修复 2：测试通知接口

在 `test_notification()` 函数中也添加 OneBot：

```python
@router.get("/test")
async def test_notification():
    # 从配置文件获取通知配置
    onebot_config = config_storage.get("onebot", {})  # ← 新增
    
    notification_config = {
        "telegram": {...},
        "wecom": wecom_config,
        "discord": discord_config,
        "onebot": onebot_config  # ← 新增
    }
```

## 使用说明

### 配置 OneBot

1. 访问通知配置页面
2. 填写 OneBot 配置：
   - **HTTP URL**：OneBot 实现的 HTTP API 地址（如：`http://localhost:3000`）
   - **Access Token**：访问令牌（可选）
   - **群组ID**：接收报告的QQ群号列表（如：`123456,789012`）
   - **用户ID**：接收报告的QQ号列表（如：`987654321`）

3. 在报告推送配置中勾选 **OneBot** 渠道

### 定时任务

配置完成后，定时任务会自动：
- 每日/每周/每月按计划生成报告
- 将报告图片发送到配置的QQ群和用户
- 如果图片生成失败，会回退到文本版本

### Emby Webhook 实时通知

配置完成后，Emby 事件会实时推送到 QQ：
- 📺 有人开始播放电影/剧集时
- 📚 新电影/剧集入库时
- 🔐 用户登录成功/失败时
- ⭐ 用户收藏/评分/标记已观看时

通知会自动发送到配置的所有群组和用户。

### 手动发送与测试

### 手动发送与测试

- **手动报告发送**：通过前端页面手动触发报告发送
- **测试通知**：访问 `/api/webhook/test` 接口测试配置

## 通知流程说明

### 定时报告推送流程

```
定时任务触发
  ↓
生成报告数据
  ↓
生成报告图片（Playwright 或 PIL）
  ↓
读取通知配置（包括 OneBot）
  ↓
发送到各个渠道
  ├─ Telegram (图片)
  ├─ 企业微信 (图片)
  ├─ Discord (图片)
  └─ OneBot (图片 base64) ← 新增
```

### Emby Webhook 实时通知流程

```
Emby 事件触发（播放/入库/登录/收藏等）
  ↓
Webhook 发送到 /api/webhook/emby
  ↓
解析事件数据，构建上下文
  ↓
获取 TMDB 图片（如果有）
  ↓
渲染通知模板
  ↓
读取通知配置（包括 OneBot）
  ↓
发送到所有渠道
  ├─ Telegram (文本+图片URL)
  ├─ 企业微信 (图文消息)
  ├─ Discord (Embed)
  └─ OneBot (文本+图片URL) ← 新增
```

## 测试建议

### 1. 基础配置测试
1. 配置 OneBot 连接信息（HTTP URL、群组ID等）
2. 访问 `/api/webhook/test` 测试接口
3. 检查 QQ 群是否收到测试消息

### 2. 手动报告测试
1. 在前端手动生成报告
2. 勾选 OneBot 渠道
3. 发送报告，检查 QQ 是否收到图片

### 3. 定时任务测试
1. 配置每日/每周/每月报告时间
2. 勾选 OneBot 渠道
3. 等待定时任务触发或手动重启服务

### 4. Webhook 事件测试
1. 在 Emby 中配置 Webhook URL：`http://your-server:8899/api/webhook/emby`
2. 播放一部电影或剧集
3. 检查 QQ 是否收到播放通知
4. 测试入库、登录、收藏等其他事件

## OneBot 实现说明

理论上支持所有遵循 [OneBot v11](https://github.com/botuniverse/onebot-11) 标准的实现：
- [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)
- [Lagrange.OneBot](https://github.com/LagrangeDev/Lagrange.Core)
- [OpenShamrock](https://github.com/whitechi73/OpenShamrock)

### 发送方式

- **图片报告**：使用 base64 编码上传图片
- **文本报告**：发送纯文本消息（带图片URL，如果有）

### API 调用

```python
# 发送到群组
POST {http_url}/send_group_msg
{
  "group_id": 123456,
  "message": [
    {"type": "text", "data": {"text": "标题"}},
    {"type": "image", "data": {"file": "base64://..."}}
  ]
}

# 发送到私聊
POST {http_url}/send_private_msg
{
  "user_id": 987654321,
  "message": [...]
## OneBot 实现说明

### 支持的 OneBot 实现

理论上支持所有遵循 [OneBot v11](https://github.com/botuniverse/onebot-11) 标准的实现：
- [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)
- [Lagrange.OneBot](https://github.com/LagrangeDev/Lagrange.Core)
- [OpenShamrock](https://github.com/whitechi73/OpenShamrock)

### 发送方式

- **定时报告图片**：使用 base64 编码上传图片
- **Webhook 实时通知**：发送文本消息（带图片URL，如果有TMDB）

### API 调用

```python
# 发送到群组
POST {http_url}/send_group_msg
{
  "group_id": 123456,
  "message": [
    {"type": "text", "data": {"text": "标题"}},
    {"type": "image", "data": {"file": "base64://..."}}  # 或 URL
  ]
}

# 发送到私聊
POST {http_url}/send_private_msg
{
  "user_id": 987654321,
  "message": [...]
}
```

## 注意事项

- OneBot 需要提前部署并运行（如 go-cqhttp、NapCatQQ）
- 确保 HTTP URL 可从后端访问
- 定时报告使用 base64 编码图片，较大图片可能有限制
- Webhook 通知使用 URL 图片（来自TMDB），更稳定
- 如果 base64 发送失败，OneBot 实现可能支持其他方式

## 相关文件

### 本次修改
- `backend/services/scheduler.py` - 定时任务调度器（已添加 OneBot）
- `backend/routers/webhook.py` - Webhook 路由（已添加 OneBot）

### 已有实现
- `backend/services/notification.py` - OneBot 发送实现
- `backend/routers/config.py` - OneBot 配置定义
- `backend/routers/report.py` - 手动发送接口

## 功能对比

| 功能 | 修复前 | 修复后 |
|------|--------|--------|
| 手动发送报告 | ✅ 支持 | ✅ 支持 |
| 定时报告推送 | ❌ 不支持 | ✅ 支持 |
| Webhook 实时通知 | ❌ 不支持 | ✅ 支持 |
| 测试通知接口 | ❌ 不支持 | ✅ 支持 |

## 支持的事件类型

### 定时报告
- 📊 每日观影报告
- 📊 每周观影报告
- 📊 每月观影报告

### Webhook 实时通知
- 📺 播放开始/暂停/继续/停止
- 📚 新内容入库
- 🔐 用户登录成功/失败
- ⭐ 收藏/取消收藏
- ⭐ 评分更新
- ✓ 标记已播放/未播放

---

**修复日期：** 2025-12-16  
**影响范围：** 定时报告 + Webhook 实时通知  
**兼容性：** 向后兼容，不影响现有功能  
**测试状态：** 待测试

