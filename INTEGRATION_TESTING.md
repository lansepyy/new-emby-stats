# Emby Stats Beta - Docker 集成测试文档

本文档描述了 Emby Stats Beta 项目的 Docker 镜像构建和集成测试流程。

## 📋 目录

- [概述](#概述)
- [测试环境要求](#测试环境要求)
- [快速开始](#快速开始)
- [详细测试流程](#详细测试流程)
- [测试覆盖范围](#测试覆盖范围)
- [常见问题](#常见问题)
- [测试报告解读](#测试报告解读)

## 概述

集成测试验证了以下内容：

1. ✅ **Docker 镜像构建** - 前后端代码正确打包
2. ✅ **容器启动** - 应用能正常运行
3. ✅ **通知功能** - 新增的通知系统 API 完整性
4. ✅ **原有功能** - 统计、用户、设备等核心功能
5. ✅ **前端访问** - Web 界面和 PWA 功能

## 测试环境要求

### 必需软件

- **Docker**: >= 20.10
- **Python 3**: >= 3.8 (用于运行测试脚本)
- **Bash**: 用于运行自动化脚本

### Python 依赖

测试脚本需要以下 Python 包：

```bash
pip install requests
```

## 快速开始

### 方法一：自动化测试脚本（推荐）

运行完整的自动化测试流程：

```bash
# 赋予执行权限
chmod +x docker-integration-test.sh

# 运行测试
./docker-integration-test.sh
```

测试脚本会自动完成：
1. 检查 Docker 环境
2. 构建镜像
3. 启动容器
4. 运行集成测试
5. 生成测试报告
6. 清理环境

### 方法二：手动测试

#### 1. 构建镜像

```bash
docker build -t emby-stats-beta .
```

#### 2. 启动容器

```bash
# 创建测试目录
mkdir -p /tmp/emby-test-config
mkdir -p /tmp/emby-test-data

# 创建空数据库文件
touch /tmp/emby-test-data/playback_reporting.db
touch /tmp/emby-test-data/users.db
touch /tmp/emby-test-data/authentication.db

# 启动容器
docker run -d \
  --name emby-stats-test \
  -p 8899:8000 \
  -v /tmp/emby-test-config:/config \
  -v /tmp/emby-test-data:/data:ro \
  -e TZ=Asia/Shanghai \
  -e PLAYBACK_DB=/data/playback_reporting.db \
  -e USERS_DB=/data/users.db \
  -e AUTH_DB=/data/authentication.db \
  -e EMBY_URL=http://localhost:8096 \
  emby-stats-beta
```

#### 3. 检查容器状态

```bash
# 查看容器运行状态
docker ps

# 查看日志
docker logs emby-stats-test
```

#### 4. 运行测试

```bash
# 安装依赖
pip install requests

# 运行测试脚本
python3 integration_test.py --url http://localhost:8899
```

#### 5. 清理

```bash
# 停止并删除容器
docker stop emby-stats-test
docker rm emby-stats-test

# 清理测试数据
rm -rf /tmp/emby-test-config /tmp/emby-test-data
```

## 详细测试流程

### 阶段 1: Docker 镜像构建

**目标**: 确保多阶段构建成功，前后端代码正确打包

**验证点**:
- ✅ Node.js 前端构建阶段无错误
- ✅ Python 依赖安装成功
- ✅ 前端 dist 目录正确复制到最终镜像
- ✅ 镜像大小合理

**预期输出**:
```
Successfully built [image-id]
Successfully tagged emby-stats-beta:latest
```

### 阶段 2: 容器启动与健康检查

**目标**: 验证容器能正常启动，应用可访问

**验证点**:
- ✅ 容器状态为 "Up"
- ✅ 端口映射正确 (8899:8000)
- ✅ 日志无致命错误
- ✅ HTTP 服务响应正常

**检查命令**:
```bash
# 容器状态
docker ps --filter "name=emby-stats-test"

# 实时日志
docker logs -f emby-stats-test

# 健康检查
curl http://localhost:8899/
```

### 阶段 3: 通知功能集成测试

测试新增的通知系统 API 端点。

#### 3.1 GET /api/notifications

**测试**: 获取完整通知配置（设置 + 模板 + 配置）

**验证点**:
- ✅ 返回结构包含 `settings`, `templates`, `config`, `history`
- ✅ `config` 包含所有通道: emby, telegram, discord, wecom, tmdb
- ✅ 模板列表非空

**示例请求**:
```bash
curl http://localhost:8899/api/notifications
```

**预期响应结构**:
```json
{
  "settings": [],
  "templates": [
    {
      "id": "default",
      "name": "Default",
      "subject": "...",
      "body": "...",
      "template_type": "default",
      "variables": []
    }
  ],
  "config": {
    "emby": { "enabled": false, ... },
    "telegram": { "enabled": false, ... },
    "discord": { "enabled": false, ... },
    "wecom": { "enabled": false, ... },
    "tmdb": { "enabled": false, ... }
  },
  "history": []
}
```

#### 3.2 GET /api/notifications/settings

**测试**: 获取通知设置（后端格式）

**验证点**:
- ✅ 返回 `success: true`
- ✅ `data` 包含后端设置结构

**示例请求**:
```bash
curl http://localhost:8899/api/notifications/settings
```

#### 3.3 POST /api/notifications/settings

**测试**: 保存通知配置（前端格式）

**验证点**:
- ✅ 接受前端格式的通道配置
- ✅ 正确转换并保存到后端格式
- ✅ 返回成功状态

**示例请求**:
```bash
curl -X POST http://localhost:8899/api/notifications/settings \
  -H "Content-Type: application/json" \
  -d '[{
    "conditions": {
      "telegram": {
        "enabled": true,
        "bot_token": "test_token",
        "admin_users": ["123456"],
        "regular_users": []
      }
    }
  }]'
```

**预期响应**:
```json
{
  "status": "success",
  "message": "设置已保存"
}
```

#### 3.4 PUT /api/notifications/settings

**测试**: 更新部分通知设置

**验证点**:
- ✅ 支持部分字段更新
- ✅ 保留未修改的字段
- ✅ 返回更新后的完整设置

**示例请求**:
```bash
curl -X PUT http://localhost:8899/api/notifications/settings \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_enabled": true,
    "telegram_bot_token": "new_token"
  }'
```

#### 3.5 GET /api/notifications/templates

**测试**: 获取所有通知模板

**验证点**:
- ✅ 返回所有模板类型: default, playback, login, mark, library
- ✅ 每个模板包含 title, text, image_template

**示例请求**:
```bash
curl http://localhost:8899/api/notifications/templates
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "default": {
      "title": "...",
      "text": "...",
      "image_template": null
    },
    "playback": { ... },
    "login": { ... }
  }
}
```

#### 3.6 PUT /api/notifications/templates/{template_id}

**测试**: 更新指定模板

**验证点**:
- ✅ 支持更新 title, text, image_template
- ✅ 验证字段长度限制
- ✅ 只允许有效的 template_id

**示例请求**:
```bash
curl -X PUT http://localhost:8899/api/notifications/templates/default \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Title",
    "text": "Test content with {{ variable }}",
    "image_template": null
  }'
```

#### 3.7 POST /api/notifications/templates/preview

**测试**: 预览模板渲染结果

**验证点**:
- ✅ 使用提供的数据渲染模板
- ✅ 返回渲染前后的内容对比
- ✅ 支持 Jinja2 模板变量

**示例请求**:
```bash
curl -X POST http://localhost:8899/api/notifications/templates/preview \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "default",
    "content": {
      "message": "Test message",
      "user": "Test User"
    }
  }'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "template_id": "default",
    "original_title": "{{ message }}",
    "original_text": "User: {{ user }}",
    "rendered_title": "Test message",
    "rendered_text": "User: Test User",
    "sample_data": { ... }
  }
}
```

### 阶段 4: 原有功能完整性验证

测试原有的统计和媒体管理功能，确保没有功能退化。

#### 4.1 统计 API

| 端点 | 描述 | 验证点 |
|------|------|--------|
| `GET /api/stats/overview` | 概览数据 | 返回总体统计信息 |
| `GET /api/stats/users` | 用户统计 | 返回用户列表和播放数据 |
| `GET /api/stats/content` | 内容统计 | 返回电影/剧集排行 |
| `GET /api/stats/devices` | 设备统计 | 返回客户端和设备信息 |
| `GET /api/stats/history` | 历史记录 | 返回播放历史列表 |

#### 4.2 媒体 API

| 端点 | 描述 | 验证点 |
|------|------|--------|
| `GET /api/media/emby-users` | Emby 用户列表 | 返回用户信息（需 Emby 连接）|
| `GET /api/media/servers` | 服务器列表 | 返回配置的服务器 |
| `GET /api/media/name-mappings` | 名称映射 | 返回客户端/设备名称映射 |

#### 4.3 认证 API

| 端点 | 描述 | 验证点 |
|------|------|--------|
| `GET /api/auth/check` | 检查登录状态 | 返回认证状态 |

### 阶段 5: 前端功能验证

#### 5.1 Web 界面访问

**测试**: http://localhost:8899/

**验证点**:
- ✅ 返回 HTML 页面
- ✅ 页面包含 React 应用挂载点
- ✅ 静态资源加载成功

#### 5.2 PWA 功能

**测试**: 
- http://localhost:8899/manifest.json
- http://localhost:8899/sw.js

**验证点**:
- ✅ manifest.json 包含 PWA 元数据
- ✅ Service Worker 文件可访问

## 测试覆盖范围

### API 端点覆盖

测试脚本覆盖 **20+ API 端点**:

**通知相关** (7 个):
- ✅ GET /api/notifications
- ✅ GET /api/notifications/settings
- ✅ POST /api/notifications/settings
- ✅ PUT /api/notifications/settings
- ✅ GET /api/notifications/templates
- ✅ PUT /api/notifications/templates/{id}
- ✅ POST /api/notifications/templates/preview

**统计相关** (5 个):
- ✅ GET /api/stats/overview
- ✅ GET /api/stats/users
- ✅ GET /api/stats/content
- ✅ GET /api/stats/devices
- ✅ GET /api/stats/history

**媒体相关** (3 个):
- ✅ GET /api/media/emby-users
- ✅ GET /api/media/servers
- ✅ GET /api/media/name-mappings

**认证相关** (1 个):
- ✅ GET /api/auth/check

**前端** (2 个):
- ✅ GET / (主页面)
- ✅ GET /manifest.json (PWA)

### 功能测试矩阵

| 功能模块 | 测试项 | 状态 |
|----------|--------|------|
| **Docker 构建** | 多阶段构建 | ✅ |
| | 前端打包 | ✅ |
| | 依赖安装 | ✅ |
| **容器运行** | 启动成功 | ✅ |
| | 端口映射 | ✅ |
| | 卷挂载 | ✅ |
| | 环境变量 | ✅ |
| **通知功能** | 获取配置 | ✅ |
| | 保存配置 | ✅ |
| | 模板管理 | ✅ |
| | 模板预览 | ✅ |
| | 多渠道支持 | ✅ |
| **统计功能** | 概览数据 | ✅ |
| | 用户统计 | ✅ |
| | 内容排行 | ✅ |
| | 设备统计 | ✅ |
| | 历史记录 | ✅ |
| **前端** | 页面加载 | ✅ |
| | PWA 支持 | ✅ |
| | 静态资源 | ✅ |

## 常见问题

### Q1: 测试脚本报错 "Service failed to start within timeout"

**原因**: 容器启动时间过长或端口被占用

**解决方案**:
```bash
# 检查端口占用
lsof -i :8899

# 增加超时时间
python3 integration_test.py --timeout 120

# 查看容器日志
docker logs emby-stats-test
```

### Q2: Docker 构建失败

**原因**: 网络问题或依赖下载失败

**解决方案**:
```bash
# 清理 Docker 缓存
docker builder prune

# 使用国内镜像加速
# 编辑 /etc/docker/daemon.json 添加:
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com"
  ]
}

# 重启 Docker
sudo systemctl restart docker
```

### Q3: 测试部分失败

**原因**: 某些测试依赖 Emby 服务器连接

**预期行为**: 
- Emby 相关测试可能返回 500（无服务器配置）
- 这是正常现象，测试脚本会标记为 "expected"

**验证**: 查看测试报告中的详细错误信息

### Q4: 权限错误

**原因**: Docker 需要 sudo 权限或用户不在 docker 组

**解决方案**:
```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker

# 或使用 sudo 运行测试
sudo ./docker-integration-test.sh
```

## 测试报告解读

### 报告文件

测试完成后会生成两个文件：

1. **integration_test_report.json** - JSON 格式的详细报告
2. **docker_container_logs.txt** - 容器完整日志

### JSON 报告结构

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "total_tests": 20,
  "passed": 18,
  "failed": 2,
  "pass_rate": 90.0,
  "results": [
    {
      "name": "GET /api/notifications",
      "status": "PASS",
      "message": "Found 5 templates and 5 channels"
    },
    {
      "name": "GET /api/media/emby-users",
      "status": "FAIL",
      "message": "Status code: 500"
    }
  ]
}
```

### 通过率标准

- **100%**: 完美，所有功能正常
- **90-99%**: 优秀，可能有 Emby 连接相关的预期失败
- **80-89%**: 良好，需要检查失败的测试
- **< 80%**: 需要修复，有重大问题

### 日志分析

查看容器日志中的关键信息：

```bash
# 查看错误
grep -i error docker_container_logs.txt

# 查看警告
grep -i warning docker_container_logs.txt

# 查看启动信息
grep -i "uvicorn" docker_container_logs.txt
```

## 脚本选项

### docker-integration-test.sh 选项

```bash
# 跳过镜像构建（使用现有镜像）
./docker-integration-test.sh --no-build

# 测试后保持容器运行
./docker-integration-test.sh --keep-container

# 使用自定义端口
./docker-integration-test.sh --port 9000

# 显示帮助
./docker-integration-test.sh --help
```

### integration_test.py 选项

```bash
# 使用自定义 URL
python3 integration_test.py --url http://localhost:9000

# 设置超时时间
python3 integration_test.py --timeout 120

# 显示帮助
python3 integration_test.py --help
```

## 持续集成

### 在 CI/CD 中使用

```yaml
# GitHub Actions 示例
name: Integration Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Run integration tests
        run: |
          chmod +x docker-integration-test.sh
          ./docker-integration-test.sh
      
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-report
          path: |
            integration_test_report.json
            docker_container_logs.txt
```

## 结论

本集成测试系统提供了：

✅ **自动化** - 一键完成构建、测试、清理  
✅ **全面性** - 覆盖 20+ API 端点和多个功能模块  
✅ **可靠性** - 详细的日志和报告  
✅ **灵活性** - 支持多种运行模式和配置  

通过这些测试，我们确保 Emby Stats Beta 的 Docker 镜像能够正确构建和运行，所有核心功能（包括新增的通知系统）都能正常工作。

## 联系与支持

如有问题或建议，请：
- 查看项目 README 和 DEVELOPMENT 文档
- 提交 Issue 到项目仓库
- 查看容器日志获取详细错误信息
