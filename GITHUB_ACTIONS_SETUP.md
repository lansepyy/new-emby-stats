# GitHub Actions 自动构建 Docker 镜像

## 配置步骤

### 1. 创建 Docker Hub Token（可选）

如果要推送到 Docker Hub：

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击右上角头像 → Account Settings
3. 左侧菜单选择 Security
4. 点击 "New Access Token"
5. 输入描述（如：GitHub Actions）
6. 复制生成的 Token

### 2. 配置 GitHub Secrets

在你的 GitHub 仓库中：

1. 进入仓库页面
2. 点击 Settings → Secrets and variables → Actions
3. 点击 "New repository secret"
4. 添加以下 Secrets：

#### 必需（如果推送到 Docker Hub）：
- **Name**: `DOCKERHUB_USERNAME`
  - **Value**: 你的 Docker Hub 用户名

- **Name**: `DOCKERHUB_TOKEN`
  - **Value**: 你的 Docker Hub Token

#### 可选（GitHub Container Registry 自动使用 GITHUB_TOKEN）：
- GHCR 推送会自动使用内置的 `GITHUB_TOKEN`，无需额外配置

### 3. 推送代码触发构建

```bash
# 推送到主分支触发构建
git add .
git commit -m "Add GitHub Actions workflow"
git push origin main

# 或创建版本标签
git tag v1.0.0
git push origin v1.0.0
```

## 触发条件

### 自动触发
- ✅ 推送到 `main` 或 `master` 分支
- ✅ 创建以 `v` 开头的标签（如 `v1.0.0`）
- ✅ 创建 Pull Request

### 手动触发
- ✅ 在 GitHub Actions 页面点击 "Run workflow"

## 构建的镜像标签

### 推送到主分支
```
your-username/emby-stats:latest
your-username/emby-stats:main
ghcr.io/your-username/emby-stats:latest
ghcr.io/your-username/emby-stats:main
```

### 推送版本标签 v1.2.3
```
your-username/emby-stats:1.2.3
your-username/emby-stats:1.2
your-username/emby-stats:1
your-username/emby-stats:v1.2.3
ghcr.io/your-username/emby-stats:1.2.3
ghcr.io/your-username/emby-stats:1.2
ghcr.io/your-username/emby-stats:1
ghcr.io/your-username/emby-stats:v1.2.3
```

## 支持的平台

- ✅ linux/amd64 (x86_64)
- ✅ linux/arm64 (ARM64/树莓派等)

## 使用构建的镜像

### 从 Docker Hub 拉取
```bash
docker pull your-username/emby-stats:latest
```

### 从 GitHub Container Registry 拉取
```bash
docker pull ghcr.io/your-username/your-repo:latest
```

### 在 docker-compose.yml 中使用
```yaml
services:
  emby-stats:
    image: your-username/emby-stats:latest
    # 或
    # image: ghcr.io/your-username/your-repo:latest
    ports:
      - "8899:8000"
    volumes:
      - ./emby-data:/emby-data:ro
      - emby-stats-data:/data
    environment:
      - EMBY_DB_PATH=/emby-data/library.db
```

## 查看构建状态

1. 进入仓库的 Actions 标签页
2. 查看最新的 "Build Docker Image" 工作流
3. 点击查看详细日志

## 仅使用 GitHub Container Registry

如果不想推送到 Docker Hub，可以删除工作流文件中的相关步骤：

1. 打开 `.github/workflows/docker-build.yml`
2. 删除或注释掉 "登录Docker Hub" 步骤
3. 在 "提取Docker元数据" 的 `images` 中删除 Docker Hub 相关行
4. 不需要配置 DOCKERHUB_USERNAME 和 DOCKERHUB_TOKEN

## 故障排除

### 构建失败
- 检查 Dockerfile 语法
- 检查 requirements.txt 和 package.json
- 查看 Actions 日志获取详细错误信息

### 推送失败
- 确认 Docker Hub Token 权限（需要 Read & Write）
- 确认 Secrets 配置正确
- 检查用户名拼写

### GHCR 推送失败
- 确认仓库 Settings → Actions → General 中的 Workflow permissions 设置为 "Read and write permissions"

## 示例：完整发布流程

```bash
# 1. 开发完成，提交代码
git add .
git commit -m "feat: 添加新功能"
git push origin main

# 2. 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 3. GitHub Actions 自动构建并推送
# 等待几分钟，在 Actions 页面查看构建进度

# 4. 拉取并使用镜像
docker pull your-username/emby-stats:1.0.0
docker-compose up -d
```

## 高级配置

### 仅在特定文件修改时触发
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'frontend/**'
      - 'Dockerfile'
      - 'docker-compose.yml'
```

### 添加构建通知
可以集成 Slack、Discord 等通知服务，在构建成功/失败时发送通知。

### 多阶段部署
可以配置自动部署到测试/生产环境。
