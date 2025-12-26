# 媒体库封面生成功能

## 功能介绍

新增的媒体库封面生成功能整合了 `jellyfin-library-poster` 和 `MoviePilot-Plugins` 的封面生成能力，可以为 Emby/Jellyfin 媒体库自动生成精美的自定义封面。

## 主要特性

### 🎨 多种封面风格

#### 1. 多图拼贴风格 (Multi)
- 基于 jellyfin-library-poster 实现
- 3×3 海报阵列，旋转排列
- 自动提取主色调生成渐变背景
- 支持马卡龙配色方案
- 可调节海报数量（6/9/12张）
- 支持背景模糊效果
- 添加阴影和圆角效果

#### 2. 马卡龙风格 (Single)
- 基于 MoviePilot-Plugins 实现
- 单张随机海报作为主图
- 智能提取马卡龙色系
- 模糊背景 + 颜色混合
- 可选胶片颗粒效果
- 可调节模糊强度和颜色比例

### ✨ 核心功能

- **智能配色**：自动提取海报主色调，过滤黑白灰
- **马卡龙调色**：将颜色调整为柔和的马卡龙风格
- **HSL 颜色空间判断**：确保背景色既不过暗也不过亮
- **渐变背景**：从左到右的渐变效果
- **阴影效果**：为海报添加立体阴影
- **圆角处理**：现代化的圆角设计
- **胶片颗粒**：复古胶片质感（单图风格）

## 使用方法

### 1. 访问封面页面

登录后，点击导航栏的"封面"标签页。

### 2. 选择媒体库

页面会自动加载所有 Emby 媒体库，点击任意媒体库的"生成封面"按钮。

### 3. 配置参数

#### 多图拼贴风格配置

- **标题**：封面上显示的标题（默认使用媒体库名称）
- **副标题**：可选的副标题文字
- **海报数量**：6/9/12 张（通过滑块调节）
- **背景模糊**：是否对背景进行模糊处理
- **马卡龙配色**：是否启用马卡龙色彩调整

#### 马卡龙风格配置

- **标题**：封面上显示的标题
- **模糊强度**：背景模糊程度（20-100）
- **颜色比例**：原图与纯色的混合比例（0.5-1.0）
- **胶片颗粒**：是否添加胶片颗粒效果

### 4. 生成预览

点击"生成预览"按钮，系统会：
1. 从媒体库获取最新的海报
2. 下载海报图片
3. 应用所选风格和配置
4. 生成封面并显示预览

### 5. 保存封面

- **下载**：将生成的封面保存到本地
- **上传**：将封面上传到 Emby 服务器（待实现）

## 技术实现

### 后端服务

**文件位置**: `backend/services/cover_generator.py`

核心类：
```python
class CoverGeneratorService:
    - get_library_list()           # 获取媒体库列表
    - get_library_items()          # 获取媒体库项目
    - download_poster()            # 下载海报
    - generate_style_multi()       # 生成多图风格
    - generate_style_single()      # 生成单图风格
```

### API 接口

**文件位置**: `backend/routers/cover.py`

端点：
- `GET /api/cover/libraries` - 获取媒体库列表
- `POST /api/cover/generate` - 生成封面
- `GET /api/cover/preview/{library_id}` - 预览媒体库项目
- `POST /api/cover/upload/{library_id}` - 上传封面到 Emby

### 前端组件

**文件位置**: `frontend/src/pages/Covers.tsx`

功能：
- 媒体库列表展示
- 配置面板（Modal）
- 实时预览
- 下载/上传操作

## 图像处理算法

### 马卡龙配色算法

```python
def adjust_color_macaron(color):
    """
    调整颜色为马卡龙风格：
    - 饱和度调整到 30%-70%
    - 亮度调整到 60%-85%
    - 使用 HSV 颜色空间
    """
```

### 渐变背景生成

```python
def create_gradient_background(width, height, color):
    """
    创建左深右浅的渐变背景：
    - 左侧颜色 = 基础色 * 0.7
    - 右侧颜色 = 基础色
    - 使用 HSL 判断颜色亮度适合度
    """
```

### 阴影效果

```python
def add_shadow(img, offset, shadow_color, blur_radius):
    """
    添加阴影：
    - 创建透明画布
    - 绘制阴影层
    - 高斯模糊
    - Alpha 合成
    """
```

## 依赖安装

项目已添加必要的 Python 依赖：

```txt
Pillow==10.1.0      # 图像处理
numpy==1.24.3       # 数值计算（胶片颗粒）
httpx==0.25.2       # 异步 HTTP 客户端
```

## 字体配置

将字体文件放在 `res/fonts/` 目录：

- `title.ttf` - 标题字体
- `subtitle.ttf` - 副标题字体

推荐免费商用字体：
- 思源黑体 (Source Han Sans)
- 阿里巴巴普惠体
- 站酷高端黑

详见 `res/fonts/README.md`

## 待实现功能

- [ ] 上传封面到 Emby 服务器
- [ ] 更多封面风格（如动态 GIF）
- [ ] 自定义背景图片
- [ ] 字体大小、颜色的更多自定义选项
- [ ] 批量生成封面
- [ ] 定时自动更新封面
- [ ] 封面模板库

## 故障排除

### 问题：无法显示中文

**解决方案**：安装中文字体到 `res/fonts/` 目录

### 问题：生成封面失败

可能原因：
1. Emby API Key 未配置
2. 媒体库中没有海报
3. 网络连接问题

**解决方案**：检查日志，确认 Emby 连接正常

### 问题：封面颜色不理想

**解决方案**：
1. 尝试切换风格
2. 调整马卡龙配色选项
3. 修改颜色比例参数

## 代码参考

本功能整合了以下开源项目的代码：

1. **jellyfin-library-poster**
   - 作者：HappyQuQu
   - 仓库：https://github.com/HappyQuQu/jellyfin-library-poster
   - 用途：多图拼贴风格的核心算法

2. **MoviePilot-Plugins**
   - 作者：justzerock
   - 仓库：https://github.com/justzerock/MoviePilot-Plugins
   - 用途：马卡龙配色和单图风格算法

感谢这些优秀的开源项目！

## 更新日志

### v1.0 (2025-12-26)
- ✨ 新增媒体库封面生成功能
- ✨ 支持多图拼贴和马卡龙两种风格
- ✨ 智能配色和渐变背景
- ✨ 实时预览和下载功能
- 📝 完善文档和使用说明
