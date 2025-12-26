# 媒体库封面生成 - 快速开始

## 🚀 快速开始

### 1. 安装字体（可选但推荐）

```bash
# 进入字体目录
cd res/fonts

# 下载思源黑体（推荐）
wget https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansCN.zip
unzip SourceHanSansCN.zip

# 重命名字体文件
cp SourceHanSansCN/OTF/SimplifiedChinese/SourceHanSansCN-Bold.otf title.ttf
cp SourceHanSansCN/OTF/SimplifiedChinese/SourceHanSansCN-Regular.otf subtitle.ttf
```

或手动下载字体放到 `res/fonts/` 目录。

### 2. 启动服务

如果使用 Docker Compose：

```bash
# 停止并重新构建
docker-compose down
docker-compose build
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 使用封面生成功能

1. 访问 http://localhost:8899
2. 使用 Emby 管理员账号登录
3. 点击顶部导航的"封面"标签
4. 选择要生成封面的媒体库
5. 配置封面参数：
   - 选择风格（多图拼贴 / 马卡龙）
   - 调整标题和其他参数
6. 点击"生成预览"
7. 满意后点击"下载"保存

## 📸 效果预览

### 多图拼贴风格
- 适合：电影库、剧集库
- 特点：展示多个热门内容
- 配置建议：
  - 海报数量：9 张
  - 马卡龙配色：开启
  - 背景模糊：关闭

### 马卡龙风格
- 适合：音乐库、图书馆
- 特点：柔和色彩，单一焦点
- 配置建议：
  - 模糊强度：50-70
  - 颜色比例：0.7-0.8
  - 胶片颗粒：开启

## 🎨 风格对比

| 特性 | 多图拼贴 | 马卡龙 |
|------|---------|--------|
| 海报数量 | 6-12张 | 1张 |
| 背景 | 渐变 | 模糊+渐变 |
| 视觉效果 | 丰富热闹 | 简约优雅 |
| 生成速度 | 较慢 | 较快 |
| 适用场景 | 影视库 | 音乐/书籍 |

## 🔧 配置说明

### 多图拼贴风格参数

```json
{
  "style": "multi",
  "poster_count": 9,      // 海报数量：6, 9, 12
  "use_blur": false,      // 背景模糊
  "use_macaron": true,    // 马卡龙配色
  "title": "我的电影",    // 标题
  "subtitle": "2024"      // 副标题
}
```

### 马卡龙风格参数

```json
{
  "style": "single",
  "blur_size": 50,           // 模糊强度：20-100
  "color_ratio": 0.8,        // 颜色比例：0.5-1.0
  "use_film_grain": true,    // 胶片颗粒
  "title": "我的音乐"        // 标题
}
```

## 💡 使用技巧

### 1. 选择合适的风格

**多图拼贴适合：**
- 内容丰富的媒体库（50+ 项目）
- 想展示多样性的场景
- 电影、电视剧库

**马卡龙适合：**
- 风格统一的媒体库
- 音乐专辑、图书收藏
- 追求简约美感

### 2. 标题设置技巧

- **留空**：自动使用媒体库名称
- **简短**：建议 2-6 个字
- **中英混合**：如 "Movies 电影"
- **emoji**：如 "🎬 电影天地"

### 3. 颜色优化

如果生成的颜色不理想：

1. **多次生成**：随机算法可能产生不同效果
2. **调整马卡龙配色**：关闭后使用原始色彩
3. **修改颜色比例**：降低比例使颜色更淡

### 4. 性能优化

- **海报数量**：9 张是平衡点
- **并发生成**：避免同时生成多个封面
- **缓存清理**：定期清理 `/tmp/cover_cache`

## 🐛 常见问题

### Q: 中文显示为方块？
A: 需要安装中文字体到 `res/fonts/` 目录。

### Q: 生成速度慢？
A: 
- 减少海报数量
- 检查网络连接
- 确认 Emby 服务器响应正常

### Q: 封面颜色太暗/太亮？
A:
- 尝试切换风格
- 调整颜色比例参数
- 多生成几次（随机性）

### Q: 无法获取媒体库？
A:
- 检查 Emby API Key
- 确认用户权限
- 查看后端日志

### Q: 如何批量生成？
A: 当前版本需手动逐个生成，批量功能计划在后续版本添加。

## 📚 进阶使用

### API 调用示例

```bash
# 获取媒体库列表
curl http://localhost:8899/api/cover/libraries

# 生成封面
curl -X POST http://localhost:8899/api/cover/generate \
  -H "Content-Type: application/json" \
  -d '{
    "library_id": "abc123",
    "library_name": "Movies",
    "style": "multi",
    "poster_count": 9,
    "use_macaron": true
  }' \
  --output cover.png
```

### 自定义开发

修改 `backend/services/cover_generator.py` 可以：
- 调整默认配置
- 添加新的风格
- 自定义颜色算法
- 修改布局参数

## 🎯 最佳实践

1. **首次使用**：先用默认配置测试
2. **字体准备**：提前安装好字体
3. **标题简洁**：避免过长文字
4. **风格匹配**：根据媒体库类型选择
5. **定期更新**：随媒体库内容更新封面

## 🔗 相关链接

- [详细文档](./COVER_GENERATION.md)
- [字体安装](../res/fonts/README.md)
- [问题反馈](https://github.com/your-repo/issues)

---

**享受创建精美封面的乐趣！** 🎨
