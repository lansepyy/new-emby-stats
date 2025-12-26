# 定时推送报告功能修复说明

## 问题诊断

定时推送报告功能无法正常工作的主要原因：

### 1. **异步方法缺失**
在 `backend/services/scheduler.py` 中，调度器尝试调用以下异步方法：
- `notification_service.send_telegram_message()`
- `notification_service.send_wecom_message()`
- `notification_service.send_discord_message()`

但是 `NotificationService` 类中只定义了同步方法：
- `send_telegram()` 
- `send_wecom()`
- `send_discord()`

### 2. **方法名不匹配**
调用的方法名与实际存在的方法名不一致。

### 3. **同步HTTP请求**
原来的实现使用同步的 `requests` 库，在异步调度器中会阻塞事件循环。

## 修复内容

### 1. 修改 `backend/services/notification.py`

#### 添加异步HTTP支持
```python
import httpx  # 新增异步HTTP客户端
```

#### 将所有发送方法改为异步
- ✅ `send_all()` → `async def send_all()`
- ✅ `send_telegram()` → `async def send_telegram()`
- ✅ `send_wecom()` → `async def send_wecom()`
- ✅ `send_discord()` → `async def send_discord()`
- ✅ `_send_telegram_photo_url()` → `async def _send_telegram_photo_url()`
- ✅ `_send_telegram_photo_file()` → `async def _send_telegram_photo_file()`
- ✅ `_send_telegram_text()` → `async def _send_telegram_text()`

#### 替换HTTP请求方式
将所有 `requests` 调用改为异步的 `httpx.AsyncClient()`：

```python
# 原来：
resp = requests.post(url, data=data, timeout=15)

# 修改后：
async with httpx.AsyncClient() as client:
    resp = await client.post(url, data=data, timeout=15)
```

### 2. 修改 `backend/services/scheduler.py`

#### 修正方法调用名称
```python
# 原来：
await notification_service.send_telegram_message(report_text)
await notification_service.send_wecom_message(report_text)
await notification_service.send_discord_message(report_text)

# 修改后：
await notification_service.send_telegram(report_title, report_text)
await notification_service.send_wecom(report_title, report_text)
await notification_service.send_discord(report_title, report_text)
```

#### 添加标题参数
发送报告时现在会传递报告标题：
```python
report_title = report.get("title", "观影报告")
```

### 3. 修改 `backend/routers/webhook.py`

在webhook处理和测试通知中添加 `await`：
```python
# 原来：
notification_service.send_all(title, message, image_url)

# 修改后：
await notification_service.send_all(title, message, image_url)
```

## 如何检查修复是否生效

### 1. 检查定时任务是否启动

查看应用启动日志，应该能看到：
```
INFO: 报告调度器已启动
INFO: 每日报告任务已配置：每天 21:00
INFO: 每周报告任务已配置：每周日 21:00
INFO: 每月报告任务已配置：每月1日 21:00
```

如果没有看到任务配置信息，说明报告推送未启用，需要在配置中开启：

```json
{
  "report": {
    "enabled": true,
    "daily_enabled": true,
    "weekly_enabled": false,
    "monthly_enabled": false,
    "daily_time": "21:00",
    "channels": {
      "telegram": true,
      "wecom": false,
      "discord": false
    }
  }
}
```

### 2. 测试Webhook通知功能

访问测试接口：
```bash
GET http://your-server:8000/api/webhook/test
```

如果配置正确，应该能收到测试通知。

### 3. 手动触发报告生成

可以通过前端或API手动生成报告：
```bash
GET http://your-server:8000/api/report/generate?type=daily
```

### 4. 查看错误日志

如果仍然有问题，检查容器日志：
```bash
docker logs emby-stats-backend
```

查找以下关键词：
- "报告调度器已启动"
- "开始生成每日报告"
- "报告已通过 Telegram 发送"
- 错误信息

## 配置要求

### 最小配置示例

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "admins": ["CHAT_ID_1"],
    "users": ["CHAT_ID_2"]
  },
  "report": {
    "enabled": true,
    "daily_enabled": true,
    "daily_time": "21:00",
    "channels": {
      "telegram": true
    }
  }
}
```

### 配置文件位置

配置文件路径：`/config/webhook_config.json`

在Docker中对应的挂载路径，请检查 `docker-compose.yml`。

## 故障排查

### 问题：看不到任务配置日志

**原因**：报告推送未启用

**解决**：在配置中设置 `"report.enabled": true`

### 问题：定时到了但没有发送

**原因**：
1. 通知渠道配置不正确（如缺少 bot_token）
2. 时区问题（调度器使用系统时区）

**解决**：
1. 检查通知配置是否完整
2. 检查容器时区设置

### 问题：发送失败

**原因**：
1. 网络问题（无法访问 Telegram/企业微信/Discord API）
2. Token/Webhook 配置错误

**解决**：
1. 检查网络连接
2. 使用测试接口验证配置
3. 查看详细错误日志

## 依赖要求

确保 `backend/requirements.txt` 中包含 `httpx`：

```
httpx==0.25.2
```

如果缺少，需要重新构建Docker镜像。

## 重启应用

修复后需要重启应用以使更改生效：

```bash
docker-compose restart backend
```

或者重新构建：

```bash
docker-compose down
docker-compose build
docker-compose up -d
```
