# Emby Stats 开发文档

## 项目概述

Emby Stats 是一个现代化的 Emby 媒体服务器播放统计分析面板，提供实时播放监控、数据可视化、用户统计、观影报告生成等功能。项目采用前后端分离架构，支持多服务器管理、PWA 离线访问和 Telegram 推送集成。

### 核心功能

- **实时监控**：正在播放会话实时显示
- **数据统计**：播放次数、时长、用户、内容、设备等多维度统计
- **可视化图表**：趋势图、热力图、饼图、柱状图
- **内容排行**：热门内容展示和播放排行榜
- **观影报告**：支持每日/每周/每月/每年报告自动生成
- **Telegram 集成**：Bot 交互、用户绑定、报告推送
- **多服务器**：支持管理多个 Emby 服务器，动态切换
- **名称映射**：客户端和设备名称自定义映射
- **PWA 支持**：可安装到桌面，支持离线访问

### 技术栈

**后端：**
- Python 3.11
- FastAPI 0.104.1
- aiosqlite 0.19.0
- APScheduler 3.10.4
- Pillow 10.1.0（报告图片生成）
- python-telegram-bot 20.7
- httpx 0.25.2
- cachetools 5.3.2

**前端：**
- Vue 3.5
- TypeScript 5.6
- Vuetify 3.7（Material Design 组件库）
- Vite 6.0
- Pinia 2.2（状态管理）
- Vue Router 4.5
- ECharts 5.5（图表库）

**部署：**
- Docker（多阶段构建）
- Node.js 20（构建阶段）
- Python 3.11-slim（运行阶段）

**Docker 镜像：** `qc0624/emby-stats`

**当前版本：** v2.26

---

## 目录结构

```
emby-stats/
├── backend/                          # Python FastAPI 后端
│   ├── main.py                       # FastAPI 应用入口
│   ├── config.py                     # 环境变量配置管理
│   ├── database.py                   # 数据库工具函数
│   ├── scheduler.py                  # APScheduler 定时任务
│   ├── name_mappings.py              # 客户端/设备名称映射服务
│   ├── requirements.txt              # Python 依赖
│   ├── routers/                      # API 路由模块
│   │   ├── __init__.py
│   │   ├── auth.py                   # 认证路由（登录/登出/检查）
│   │   ├── stats.py                  # 统计数据 API（核心）
│   │   ├── media.py                  # 媒体资源（海报/背景图/内容详情/排行）
│   │   ├── servers.py                # 多服务器管理 CRUD
│   │   ├── files.py                  # 文件浏览器（选择数据库路径）
│   │   ├── report.py                 # 观影报告配置和发送
│   │   └── tg_bot.py                 # Telegram Bot 管理
│   └── services/                     # 业务逻辑服务
│       ├── emby.py                   # Emby API 交互（带缓存）
│       ├── servers.py                # 服务器管理服务
│       ├── users.py                  # 用户数据服务
│       ├── report.py                 # 报告图片生成（PIL）
│       ├── report_simple.py          # 简化版报告生成
│       ├── report_config.py          # 报告配置管理（JSON）
│       ├── telegram.py               # Telegram 推送服务
│       ├── tg_bot.py                 # Telegram Bot 交互
│       └── tg_binding.py             # TG 用户绑定管理
├── frontend-vue/                     # Vue 3 + Vuetify 前端
│   ├── public/
│   │   ├── sw.js                     # Service Worker（PWA）
│   │   ├── manifest.json             # PWA 清单
│   │   └── icons/                    # PWA 图标
│   ├── src/
│   │   ├── main.ts                   # Vue 应用入口
│   │   ├── App.vue                   # 根组件
│   │   ├── router/
│   │   │   └── index.ts              # Vue Router 配置
│   │   ├── stores/                   # Pinia 状态管理
│   │   │   ├── index.ts              # Store 导出
│   │   │   ├── auth.ts               # 认证状态
│   │   │   ├── server.ts             # 服务器选择
│   │   │   └── filter.ts             # 筛选状态（持久化）
│   │   ├── services/
│   │   │   ├── axios.ts              # Axios 实例和拦截器
│   │   │   └── api/
│   │   │       ├── auth.ts           # 认证 API
│   │   │       ├── servers.ts        # 服务器 API
│   │   │       └── stats.ts          # 统计 API
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript 类型定义
│   │   ├── layouts/
│   │   │   └── DefaultLayout.vue     # 主布局（导航/侧边栏）
│   │   ├── pages/                    # 页面组件
│   │   │   ├── Overview.vue          # 总览页面
│   │   │   ├── Content.vue           # 内容统计（热门内容+播放排行）
│   │   │   ├── ContentDetail.vue     # 内容详情
│   │   │   ├── Users.vue             # 用户统计
│   │   │   ├── Devices.vue           # 设备统计
│   │   │   ├── History.vue           # 播放历史
│   │   │   ├── Favorites.vue         # 收藏统计
│   │   │   ├── Report.vue            # 报告配置
│   │   │   └── Login.vue             # 登录页
│   │   ├── components/               # 通用组件
│   │   │   ├── FilterPanel.vue       # 筛选面板
│   │   │   ├── ServerManagementPanel.vue  # 服务器管理
│   │   │   ├── NameMappingPanel.vue  # 名称映射配置
│   │   │   ├── charts/               # 图表组件
│   │   │   │   ├── TrendChart.vue    # 趋势折线图
│   │   │   │   ├── HeatmapChart.vue  # 热力图
│   │   │   │   ├── PieChart.vue      # 饼图
│   │   │   │   └── UsersChart.vue    # 用户柱状图
│   │   │   └── ui/                   # UI 基础组件
│   │   │       ├── Card.vue          # 卡片容器
│   │   │       ├── PosterCard.vue    # 海报卡片
│   │   │       └── ...
│   │   ├── composables/              # 组合式函数
│   │   │   └── useToast.ts           # Toast 通知
│   │   ├── plugins/
│   │   │   └── vuetify.ts            # Vuetify 配置
│   │   └── utils/
│   │       └── format.ts             # 格式化工具函数
│   ├── package.json                  # npm 依赖
│   ├── vite.config.ts                # Vite 构建配置
│   ├── tsconfig.json                 # TypeScript 配置
│   └── dist/                         # 构建输出
├── Dockerfile                        # Docker 多阶段构建
├── docker-compose.yml                # Docker Compose 配置
├── .env.example                      # 环境变量示例
├── name_mappings.example.json        # 名称映射示例
├── README.md                         # 项目说明文档
├── DEVELOPMENT.md                    # 开发文档（本文件）
└── CHANGELOG.md                      # 更新日志
```

### 运行时目录

容器内的关键目录：

| 目录 | 说明 | 权限 |
|------|------|------|
| `/app` | 应用代码目录 | 只读 |
| `/app/frontend` | 前端构建产物 | 只读 |
| `/data` | Emby 数据目录（挂载） | 只读 |
| `/config` | 配置目录（挂载） | 读写 |

`/config` 目录下的文件：
- `sessions.db` - 会话数据库
- `servers.db` - 服务器配置数据库
- `tg_bindings.db` - TG 用户绑定数据库
- `tg_bot_config.json` - TG Bot 配置
- `report_config_{server_id}.json` - 各服务器的报告配置
- `name_mappings.json` - 名称映射配置

---

## 后端架构

### 1. 应用入口 (main.py)

FastAPI 应用的核心入口，负责：
- 应用实例化和中间件配置
- CORS 配置（允许所有来源）
- 认证中间件（保护 `/api/*` 路由）
- 静态文件服务（前端构建产物和 PWA 资源）
- 启动/关闭生命周期事件

**公开路径（无需认证）：**
```python
PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/check",
    "/api/auth/logout",
    "/manifest.json",
    "/sw.js",
}

PUBLIC_PREFIXES = [
    "/api/servers",      # 服务器列表（登录页需要）
    "/icons/",
    "/static/",
]
```

**启动流程：**
1. 初始化会话表 (`init_sessions_table`)
2. 初始化服务器表 (`server_service.init_servers_table`)
3. 迁移旧版配置 (`server_service.migrate_legacy_config`)
4. 初始化 TG 绑定数据库 (`tg_binding_service.init_db`)
5. 启动定时任务调度器 (`start_scheduler`)
6. 启动 Telegram Bot (`tg_bot_service.start`)

### 2. 配置管理 (config.py)

通过环境变量配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TZ` | 系统时区 | `Asia/Shanghai` |
| `PLAYBACK_DB` | 播放记录数据库路径 | `/data/playback_reporting.db` |
| `USERS_DB` | 用户数据库路径 | `/data/users.db` |
| `AUTH_DB` | 认证数据库路径 | `/data/authentication.db` |
| `EMBY_URL` | Emby 服务器地址 | `http://localhost:8096` |
| `EMBY_API_KEY` | Emby API Key（可选） | 空（自动从数据库获取） |
| `MIN_PLAY_DURATION` | 最小播放时长过滤（秒） | `0`（不过滤） |
| `TZ_OFFSET` | 时区偏移（小时） | `8`（北京时间） |

**说明：**
- `EMBY_API_KEY` 如果不填，会自动从 Emby 认证数据库获取
- `MIN_PLAY_DURATION` 用于过滤短时间播放记录，低于此时长的不计入播放次数（但时长仍统计）
- `TZ_OFFSET` 用于 SQLite 查询时的时间转换（UTC → 本地时间）

### 3. 数据库工具 (database.py)

**数据库连接函数：**
```python
get_playback_db(server_config)      # 播放记录数据库（Emby Playback Reporting 插件）
get_users_db(server_config)         # 用户数据库
get_auth_db(server_config)          # 认证数据库
get_sessions_db()                   # 会话数据库（/config/sessions.db）
```

**SQL 辅助函数：**
```python
get_count_expr()                    # 播放次数统计（支持最小时长过滤）
get_duration_filter()               # 播放时长过滤条件
local_datetime(column)              # UTC 转本地时间
local_date(column)                  # UTC 转本地日期
convert_guid_bytes_to_standard()    # .NET GUID 字节转换
```

### 4. 路由模块 (routers/)

#### stats.py - 统计 API

所有统计接口支持统一的筛选参数：
- `days` - 天数范围
- `start_date`, `end_date` - 日期范围
- `users` - 用户 ID 列表（逗号分隔）
- `clients` - 客户端列表
- `devices` - 设备列表
- `item_types` - 媒体类型
- `playback_methods` - 播放方式
- `server_id` - 服务器 ID

**主要端点：**
| 端点 | 说明 |
|------|------|
| `GET /api/overview` | 总览统计 |
| `GET /api/trend` | 播放趋势（按天） |
| `GET /api/hourly` | 按小时统计（热力图） |
| `GET /api/users` | 用户统计 |
| `GET /api/clients` | 客户端统计（支持名称映射） |
| `GET /api/devices` | 设备统计（支持名称映射） |
| `GET /api/playback-methods` | 播放方式统计 |
| `GET /api/recent` | 最近播放记录 |
| `GET /api/now-playing` | 正在播放 |
| `GET /api/filter-options` | 筛选选项 |
| `GET /api/favorites` | 收藏统计 |
| `GET /api/name-mappings` | 获取名称映射配置 |
| `POST /api/name-mappings` | 保存名称映射配置 |
| `POST /api/name-mappings/reload` | 重新加载名称映射 |

#### media.py - 媒体资源和内容统计

- `GET /api/poster/{item_id}?server_id={id}` - 获取海报（支持多服务器）
- `GET /api/backdrop/{item_id}?server_id={id}` - 获取背景图（支持多服务器）
- `GET /api/top-content` - 热门内容排行（剧集按剧名聚合，返回series_id）
- `GET /api/top-shows` - 热门剧集（按剧名聚合，返回series_id）
- `GET /api/content-detail` - 内容详情和播放记录

**重要特性：**
- 剧集自动按剧名聚合，返回 series_id 而非单集 episode_id
- 海报和背景图 URL 包含 server_id 参数，支持多服务器切换

#### auth.py - 认证

- `POST /api/auth/login` - 登录（通过 Emby API 验证）
- `GET /api/auth/check` - 检查登录状态
- `POST /api/auth/logout` - 登出

认证使用 Cookie 存储 session_id，会话存储在 SQLite。

#### servers.py - 多服务器管理

- `GET /api/servers` - 获取服务器列表
- `POST /api/servers` - 添加服务器
- `PUT /api/servers/{id}` - 更新服务器
- `DELETE /api/servers/{id}` - 删除服务器

#### report.py - 观影报告

- `GET /api/report/config` - 获取报告配置
- `POST /api/report/config` - 保存报告配置
- `GET /api/report/preview` - 预览报告图片
- `POST /api/report/send` - 手动发送报告
- `POST /api/report/test-push` - 测试 Telegram 推送
- `GET /api/report/bindings` - 获取 TG 绑定用户列表

#### files.py - 文件浏览器

- `GET /api/files?path=/` - 浏览目录

用于添加服务器时选择数据库路径。

#### tg_bot.py - Telegram Bot 管理

- `GET /api/tg-bot/config` - 获取 Bot 配置
- `POST /api/tg-bot/config` - 保存 Bot 配置

### 5. 服务模块 (services/)

#### emby.py - Emby API 服务

`EmbyService` 类：
- `get_api_key()` - 获取 API Key
- `get_item_info()` - 获取媒体信息（带 TTLCache 缓存）
- `get_poster()` / `get_backdrop()` - 获取图片
- `get_poster_url()` / `get_backdrop_url()` - 生成图片 URL（带 server_id 参数）
- `get_now_playing()` - 获取正在播放会话
- `authenticate_user()` - 用户认证

#### name_mappings.py - 名称映射服务

`NameMappingService` 类：
- `map_client_name()` - 映射客户端名称
- `map_device_name()` - 映射设备名称
- `get_all_mappings()` - 获取所有映射
- `save_mappings()` - 保存映射配置
- `reload()` - 热重载配置

支持正则表达式匹配和精确匹配。

---

## 前端架构

### 1. 技术选型

- **Vue 3 Composition API**：使用 `<script setup>` 语法
- **Vuetify 3**：Material Design 组件库
- **Pinia**：轻量级状态管理
- **Vue Router**：路由管理
- **TypeScript**：类型安全
- **ECharts**：数据可视化
- **Vite**：快速构建工具

### 2. 状态管理 (stores/)

使用 Pinia 管理全局状态：

#### auth.ts
- `isAuthenticated` - 登录状态
- `user` - 当前用户信息
- `login()` / `logout()` - 登录/登出方法
- `checkAuth()` - 检查认证状态

#### server.ts
- `servers` - 服务器列表
- `currentServer` - 当前选中服务器
- `currentServerId` - 当前服务器 ID
- `setCurrentServer()` - 切换服务器
- `fetchServers()` - 加载服务器列表

#### filter.ts
- `dateRange` - 日期范围
- `selectedUsers` - 选中的用户
- `selectedClients` - 选中的客户端
- `selectedDevices` - 选中的设备
- `selectedTypes` - 选中的媒体类型
- `searchQuery` - 搜索关键词
- `buildQueryParams` - 构建 API 查询参数
- 筛选状态持久化到 localStorage

### 3. 路由配置 (router/)

主要路由：

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | `Overview.vue` | 总览页面 |
| `/content` | `Content.vue` | 内容统计 |
| `/content/:id` | `ContentDetail.vue` | 内容详情 |
| `/users` | `Users.vue` | 用户统计 |
| `/devices` | `Devices.vue` | 设备统计 |
| `/history` | `History.vue` | 播放历史 |
| `/favorites` | `Favorites.vue` | 收藏统计 |
| `/report` | `Report.vue` | 报告配置 |
| `/login` | `Login.vue` | 登录页 |

所有路由（除 `/login`）需要认证。

### 4. 页面组件 (pages/)

#### Overview.vue - 总览页面
- 统计卡片：播放次数、时长、用户数、内容数
- 播放趋势图
- 活跃时段热力图
- 正在播放会话

#### Content.vue - 内容统计
- **热门内容**：海报墙展示（包括剧集和电影）
- **播放排行**：排行榜样式，前三名有金银铜牌效果

#### ContentDetail.vue - 内容详情
- 内容基本信息（海报、简介）
- 播放统计（次数、时长、用户数）
- 播放记录列表

#### Users.vue - 用户统计
- 用户播放排行
- 用户柱状图

#### Devices.vue - 设备统计
- 客户端分布饼图（横向图例）
- 设备分布饼图（横向图例）
- 客户端详情表格
- 设备详情表格

#### History.vue - 播放历史
- 最近播放记录
- 支持搜索和筛选
- 显示海报和详情

#### Favorites.vue - 收藏统计
- 按媒体热度排序
- 按用户收藏排序
- 双视图切换

#### Report.vue - 报告配置
- Telegram 推送设置
- 定时任务配置
- 用户选择
- 报告预览
- 测试推送按钮

#### Login.vue - 登录页
- 服务器选择
- 用户名密码登录
- 深色主题背景

### 5. 布局组件 (layouts/)

#### DefaultLayout.vue - 主布局
- 左侧导航栏（桌面端固定，移动端抽屉）
- 顶部标题栏（移动端）
- 服务器选择器
- 筛选按钮
- 主题切换
- 名称映射配置
- 登出按钮
- 版本显示：v2.26

### 6. 图表组件 (components/charts/)

#### TrendChart.vue
- 基于 ECharts 的折线图
- 显示播放次数和时长趋势
- 支持缩放和数据筛选

#### HeatmapChart.vue
- 7x24 热力图
- 显示一周各时段活跃度

#### PieChart.vue
- 基于 ECharts 的饼图
- 环形设计
- 横向图例，底部居中
- 显示百分比

#### UsersChart.vue
- 基于 ECharts 的柱状图
- 用户播放时长排行

### 7. UI 组件 (components/ui/)

#### Card.vue
- 基础卡片容器
- 使用 Vuetify v-card

#### PosterCard.vue
- 海报卡片
- 显示海报、标题、播放次数、时长
- 点击可跳转详情

#### FilterPanel.vue
- 筛选面板
- 日期范围选择
- 用户、客户端、设备选择
- 搜索功能

#### ServerManagementPanel.vue
- 服务器管理面板
- CRUD 操作
- 文件选择器

#### NameMappingPanel.vue
- 名称映射配置
- 客户端映射
- 设备映射
- 支持正则表达式

### 8. PWA 支持

#### Service Worker (public/sw.js)
- 缓存静态资源
- 网络优先策略
- 不拦截 API 请求（避免登录问题）
- 版本化缓存名称：`emby-stats-v2.26`

#### Manifest (public/manifest.json)
- PWA 清单配置
- 应用名称、图标、主题色
- 独立窗口模式

---

## 关键特性

### 1. 多服务器支持

- 每个服务器独立配置数据库路径
- 动态切换服务器无需刷新
- 海报和背景图 URL 包含 server_id 参数
- 前端通过 Cookie 存储当前服务器 ID

### 2. 名称映射

- 支持客户端和设备名称自定义映射
- 支持正则表达式匹配
- 配置实时生效，可热重载
- 在筛选选项和统计结果中自动去重

### 3. 内容聚合

- 剧集自动按剧名聚合
- 返回 series_id 而非单集 episode_id
- 海报使用剧集海报而非单集海报
- 详情页显示整部剧的统计

### 4. 排行榜设计

- 热门内容：海报墙样式
- 播放排行：列表样式，前三名金银铜牌效果
- 显示排名、海报缩略图、标题、播放次数、观看时长

### 5. PWA 离线支持

- 可安装到桌面
- 离线访问静态资源
- 自动更新检测
- Service Worker 不拦截 API 请求

---

## 开发指南

### 本地开发环境

**前置要求：**
- Python 3.11+
- Node.js 20+
- Emby 服务器（带 Playback Reporting 插件）

**后端启动：**
```bash
cd backend
pip install -r requirements.txt

# 设置环境变量
export EMBY_URL=http://your-emby:8096
export PLAYBACK_DB=/path/to/playback_reporting.db
export USERS_DB=/path/to/users.db
export AUTH_DB=/path/to/authentication.db

# 启动开发服务器
uvicorn main:app --reload --port 8000
```

**前端启动：**
```bash
cd frontend-vue
npm install
npm run dev
```

前端开发服务器默认在 `http://localhost:5173`，会自动代理 API 请求到后端。

### 添加新页面

1. 在 `frontend-vue/src/pages/` 创建 Vue 组件
2. 在 `router/index.ts` 添加路由
3. 在 `DefaultLayout.vue` 添加菜单项（如需要）

### 添加新的统计 API

1. 在 `backend/routers/stats.py` 或 `media.py` 添加路由函数
2. 使用 `build_filter_conditions()` 构建筛选条件
3. 在 `frontend-vue/src/services/api/stats.ts` 添加 API 调用
4. 在页面组件中使用

### 修改主题

在 `frontend-vue/src/plugins/vuetify.ts` 修改 Vuetify 主题配置：

```typescript
themes: {
  light: {
    colors: {
      primary: '#1976D2',
      // ...
    }
  },
  dark: {
    colors: {
      primary: '#2196F3',
      // ...
    }
  }
}
```

### Docker 构建和部署

```bash
# 构建镜像
docker build -t qc0624/emby-stats:latest .

# 本地测试
docker compose up -d

# 查看日志
docker compose logs -f

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d

# 推送到 Docker Hub
docker push qc0624/emby-stats:latest
```

---

## 版本发布流程

### 1. 更新版本号

- `frontend-vue/public/sw.js` - Service Worker 缓存版本
- `frontend-vue/src/layouts/DefaultLayout.vue` - 版本显示
- `DEVELOPMENT.md` - 当前版本号

### 2. 更新文档

- 更新 `CHANGELOG.md` 添加版本更新内容
- 更新 `README.md` 中的功能说明（如有新功能）

### 3. 构建和推送

```bash
# 构建 Docker 镜像
docker build -t qc0624/emby-stats:latest .
docker build -t qc0624/emby-stats:vX.XX .

# 推送到 Docker Hub
docker push qc0624/emby-stats:latest
docker push qc0624/emby-stats:vX.XX
```

### 4. 提交代码

```bash
git add .
git commit -m "Release vX.XX: 功能描述"
git push origin main
```

---

## 常见问题

### Q: 如何修改饼图布局？

修改 `frontend-vue/src/components/charts/PieChart.vue`，调整 `legend` 和 `center` 配置。

### Q: 如何添加名称映射？

在前端点击侧边栏的"名称映射"按钮，或直接编辑 `/config/name_mappings.json`。

### Q: 如何配置 Telegram 代理？

在报告配置页面的 Telegram 设置中填写代理地址：
- HTTP 代理：`http://127.0.0.1:7890`
- SOCKS5 代理：`socks5://127.0.0.1:1080`

### Q: PWA 更新后为什么还显示旧版本？

清除浏览器缓存或卸载 PWA 重新安装。Service Worker 会自动清理旧缓存。

### Q: 切换服务器后海报无法显示？

确保 v2.26+ 版本，海报 URL 已包含 server_id 参数。

---

## 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 无法登录 | Emby 服务器不可达 | 检查 `EMBY_URL` 配置 |
| 数据为空 | 数据库路径错误 | 检查数据库文件是否存在 |
| 海报不显示 | API Key 无效或多服务器问题 | 检查 API Key 和版本 |
| 报告发送失败 | TG Bot Token 错误 | 检查 Bot 配置和网络 |
| PWA 登录循环 | Service Worker 拦截 API | 升级到 v2.23+ |

### 日志查看

```bash
# Docker 容器日志
docker logs emby-stats

# 实时查看日志
docker logs -f emby-stats
```

---

## 贡献指南

### 代码风格

**Python：**
- 使用 4 空格缩进
- 函数和类使用 docstring 注释
- 异步函数使用 `async/await`

**TypeScript/Vue：**
- 使用 2 空格缩进
- 使用 Composition API `<script setup>` 语法
- 组件使用 PascalCase 命名
- 类型定义使用 TypeScript interface

### 提交规范

```
<type>: <description>

[optional body]
```

类型：
- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式
- `refactor` - 重构
- `perf` - 性能优化
- `chore` - 构建/工具

---

## 技术债务和改进方向

- [ ] 图表数据缓存优化
- [ ] 更多图表类型支持
- [ ] 移动端体验优化
- [ ] 多语言支持
- [ ] 更多推送渠道（邮件、企业微信等）
- [ ] 数据导出功能
- [ ] 更细粒度的权限控制
