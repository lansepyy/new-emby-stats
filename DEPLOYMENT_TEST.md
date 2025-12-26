# 部署测试指南

## 📋 前置准备

### 1. 修改配置文件

编辑 `docker-compose.test.yml`，修改以下内容：

```yaml
volumes:
  # 修改为你实际的 Emby 数据库路径
  - /path/to/emby/data/playback_reporting.db:/emby-data/playback_reporting.db:ro
  - /path/to/emby/data/users.db:/emby-data/users.db:ro
  - /path/to/emby/data/authentication.db:/emby-data/authentication.db:ro

environment:
  # 修改为你的 Emby 服务器地址
  - EMBY_URL=http://your-emby-server:8096
```

### 2. 查找 Emby 数据库位置

**Windows:**
```
C:\ProgramData\Emby-Server\data\
```

**Linux/Docker:**
```bash
docker exec emby ls -la /config/data/
```

需要的文件：
- `library.db` 或 `playback_reporting.db` - 播放记录
- `users.db` - 用户信息
- `authentication.db` - 认证信息（可选，用于自动获取 API Key）

## 🚀 部署步骤

### 方案1: 使用 docker-compose（推荐）

```bash
# 1. 拉取最新镜像
docker pull lsbobo/emby-stats:beta

# 2. 启动服务
docker-compose -f docker-compose.test.yml up -d

# 3. 查看日志
docker logs -f emby-stats-test

# 4. 访问服务
# 浏览器打开: http://localhost:8899
```

### 方案2: 直接使用 docker run

```bash
docker run -d \
  --name emby-stats-test \
  -p 8899:8000 \
  -v /path/to/emby/data/playback_reporting.db:/emby-data/playback_reporting.db:ro \
  -v /path/to/emby/data/users.db:/emby-data/users.db:ro \
  -v emby-stats-data:/data \
  -e EMBY_URL=http://your-emby-server:8096 \
  -e PLAYBACK_DB=/emby-data/playback_reporting.db \
  -e USERS_DB=/emby-data/users.db \
  -e TZ=Asia/Shanghai \
  lsbobo/emby-stats:beta
```

## ✅ 测试步骤

### 1. 检查服务状态
```bash
# 查看容器是否运行
docker ps | grep emby-stats-test

# 查看日志（检查是否有错误）
docker logs emby-stats-test
```

### 2. 测试 Web 界面
1. 访问 http://localhost:8899
2. 使用 Emby 用户名密码登录
3. 查看统计数据是否正常显示

### 3. 测试 Webhook 通知功能

#### 3.1 配置通知
1. 访问 http://localhost:8899
2. 底部导航点击 "通知" 图标（🔔）
3. 配置至少一个通知平台：
   - **Telegram**: Bot Token + Chat ID
   - **企业微信**: Corp ID + Secret + Agent ID
   - **Discord**: Webhook URL
4. 配置 TMDB API Key（可选，用于获取高清海报）
5. 点击 "保存配置"

#### 3.2 测试通知推送
1. 在通知配置页面点击 "测试通知" 按钮
2. 检查对应平台是否收到测试消息

#### 3.3 配置 Emby Webhook
1. 登录 Emby 管理后台
2. 进入 插件 → Webhook
3. 添加 Webhook URL: `http://your-server-ip:8899/api/webhook/emby`
4. 选择要监听的事件：
   - ✅ Playback Start（播放开始）
   - ✅ Playback Stop（播放结束）
   - ✅ Item Added（内容添加）
   - ✅ User Created（用户创建）
   - ✅ User Updated（用户更新）

#### 3.4 触发真实事件
1. 播放任意视频
2. 检查是否收到 "播放开始" 通知
3. 停止播放
4. 检查是否收到 "播放结束" 通知（包含播放时长）

### 4. 测试模板自定义

1. 访问 http://localhost:8899
2. 底部导航点击 "通知" → "消息模板" 标签
3. 修改任意模板（如 "播放开始"）
4. 保存后触发对应事件
5. 检查通知内容是否按新模板渲染

### 5. 检查配置持久化

```bash
# 1. 停止容器
docker stop emby-stats-test

# 2. 启动容器
docker start emby-stats-test

# 3. 访问通知页面，检查配置是否还在
```

配置文件位置：`/data/webhook_config.json`

## 🔍 故障排查

### 问题1: 无法访问 Web 界面

```bash
# 检查容器状态
docker ps -a | grep emby-stats-test

# 查看日志
docker logs emby-stats-test

# 检查端口占用
netstat -ano | findstr 8899  # Windows
ss -tlnp | grep 8899         # Linux
```

### 问题2: 登录失败

- 检查 `users.db` 路径是否正确
- 检查数据库文件权限（容器内需要可读）
- 查看日志中的错误信息

### 问题3: Webhook 不触发

```bash
# 查看实时日志
docker logs -f emby-stats-test

# 手动测试 Webhook 接口
curl -X POST http://localhost:8899/api/webhook/emby \
  -H "Content-Type: application/json" \
  -d '{"Event":"test"}'
```

检查 Emby Webhook 配置：
- URL 是否正确（注意 IP 地址）
- 事件类型是否勾选
- Emby 服务器能否访问到容器端口

### 问题4: 通知发送失败

- 检查通知平台配置是否正确
- 使用 "测试通知" 按钮验证配置
- 查看容器日志中的错误信息
- 检查网络连接（容器能否访问外网）

### 问题5: TMDB 图片不显示

- 检查 TMDB API Key 是否有效
- 查看日志中是否有 TMDB API 错误
- 确认媒体信息中包含 TMDB ID

## 📊 验证清单

- [ ] Web 界面正常访问（http://localhost:8899）
- [ ] 用户登录成功
- [ ] 统计数据正常显示
- [ ] 通知配置页面正常加载
- [ ] 保存通知配置成功
- [ ] 测试通知发送成功
- [ ] Emby Webhook 配置完成
- [ ] 播放开始事件通知正常
- [ ] 播放结束事件通知正常
- [ ] 自定义模板生效
- [ ] 配置重启后保留
- [ ] TMDB 图片正常获取（如已配置）

## 🎯 性能测试

### 1. 并发测试
```bash
# 使用 ab 工具测试
ab -n 1000 -c 10 http://localhost:8899/api/stats/overview
```

### 2. 内存占用
```bash
docker stats emby-stats-test
```

### 3. 响应时间
打开浏览器开发者工具 → Network，查看 API 请求响应时间。

## 🔄 更新镜像

```bash
# 拉取最新版本
docker pull lsbobo/emby-stats:beta

# 重新创建容器
docker-compose -f docker-compose.test.yml up -d --force-recreate

# 或者
docker stop emby-stats-test
docker rm emby-stats-test
docker-compose -f docker-compose.test.yml up -d
```

## 📝 日志收集

```bash
# 导出日志
docker logs emby-stats-test > emby-stats.log 2>&1

# 实时查看
docker logs -f --tail 100 emby-stats-test
```

## 🎉 测试完成后

如果测试通过，可以：
1. 修改 docker-compose.yml 使用正式配置
2. 创建版本标签触发正式版本构建
3. 更新 README.md 添加使用说明
4. 在 GitHub 创建 Release
