# 快速测试指南 - Emby Stats Beta

## 🚀 一键测试

```bash
# 运行完整的集成测试（推荐）
./docker-integration-test.sh
```

这将自动完成：
1. ✅ 检查 Docker 环境
2. ✅ 构建 Docker 镜像
3. ✅ 启动测试容器
4. ✅ 运行所有集成测试
5. ✅ 生成测试报告
6. ✅ 清理测试环境

## 📊 测试结果

测试完成后会生成：
- `integration_test_report.json` - 详细测试报告
- `docker_container_logs.txt` - 容器日志

## 🎯 测试覆盖

### 通知功能 API (7个)
- `GET /api/notifications` - 获取完整配置
- `GET /api/notifications/settings` - 获取设置
- `POST /api/notifications/settings` - 保存设置
- `PUT /api/notifications/settings` - 更新设置
- `GET /api/notifications/templates` - 获取模板
- `PUT /api/notifications/templates/{id}` - 更新模板
- `POST /api/notifications/templates/preview` - 预览模板

### 统计功能 API (5个)
- `GET /api/stats/overview` - 概览
- `GET /api/stats/users` - 用户统计
- `GET /api/stats/content` - 内容统计
- `GET /api/stats/devices` - 设备统计
- `GET /api/stats/history` - 历史记录

### 媒体管理 API (3个)
- `GET /api/media/emby-users` - Emby 用户
- `GET /api/media/servers` - 服务器列表
- `GET /api/media/name-mappings` - 名称映射

### 其他 (3个)
- `GET /api/auth/check` - 认证检查
- `GET /` - 前端页面
- `GET /manifest.json` - PWA 支持

## ⚙️ 高级选项

```bash
# 跳过镜像构建（使用现有镜像）
./docker-integration-test.sh --no-build

# 保持容器运行（用于调试）
./docker-integration-test.sh --keep-container

# 使用自定义端口
./docker-integration-test.sh --port 9000

# 显示帮助
./docker-integration-test.sh --help
```

## 🐛 调试模式

如需保持容器运行以进行调试：

```bash
# 启动容器并保持运行
./docker-integration-test.sh --keep-container

# 进入容器
docker exec -it emby-stats-test bash

# 查看实时日志
docker logs -f emby-stats-test

# 手动测试 API
curl http://localhost:8899/api/notifications
```

## 📝 手动测试

如需手动控制测试流程：

### 1. 构建镜像
```bash
docker build -t emby-stats-beta .
```

### 2. 启动容器
```bash
docker run -d \
  --name emby-stats-test \
  -p 8899:8000 \
  emby-stats-beta
```

### 3. 运行测试
```bash
pip install requests
python3 integration_test.py --url http://localhost:8899
```

### 4. 清理
```bash
docker stop emby-stats-test
docker rm emby-stats-test
```

## ✅ 验收标准

测试通过标准：
- ✅ Docker 镜像构建成功
- ✅ 容器正常启动
- ✅ 所有 API 端点响应正确
- ✅ 通知功能配置可保存和读取
- ✅ 原有功能无退化
- ✅ 测试通过率 >= 90%

## 🔧 常见问题

### 端口占用
```bash
# 查看端口占用
lsof -i :8899

# 使用其他端口
./docker-integration-test.sh --port 9000
```

### Docker 权限
```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

### 网络问题
```bash
# 清理 Docker 缓存
docker builder prune

# 配置镜像加速（中国大陆）
# 编辑 /etc/docker/daemon.json
```

## 📖 详细文档

查看完整文档：
- `INTEGRATION_TESTING.md` - 详细测试文档
- `DEVELOPMENT.md` - 开发指南
- `README.md` - 项目说明

## 💡 提示

1. **首次运行**需要下载依赖，可能需要 5-10 分钟
2. **测试数据库**为空，部分统计功能返回空数据是正常的
3. **Emby 连接**测试可能失败（无服务器配置），这是预期行为
4. **通知功能**是重点测试对象，确保所有端点都能正常工作

## 🎉 测试成功示例

```
================================================================================
TEST SUMMARY
================================================================================
Total Tests: 20
Passed: 20
Failed: 0
Pass Rate: 100.0%
================================================================================

✓ All integration tests passed!
Docker image: emby-stats-beta is ready for deployment
```

---

Happy Testing! 🚀
