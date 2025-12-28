# 字体配置说明

## 功能概述

新版本支持自定义中英文字体，可以分别配置中文标题字体和英文副标题字体的路径和大小。

## 使用方法

### 1. 放置字体文件

将您的自定义字体文件（支持 `.ttf`、`.otf`、`.woff`、`.woff2` 格式）放入以下目录：

```
/path/to/new-emby-stats/config/fonts/
```

例如：
```
/path/to/new-emby-stats/config/fonts/MyChineseFont.ttf
/path/to/new-emby-stats/config/fonts/MyEnglishFont.otf
```

### 2. 配置字体路径

在前端界面的 **封面生成** 页面，找到字体配置区域：

- **中文字体路径**：输入中文字体的完整路径，例如 `/config/fonts/MyChineseFont.ttf`
- **英文字体路径**：输入英文字体的完整路径，例如 `/config/fonts/MyEnglishFont.otf`

> 提示：留空则使用系统默认字体（思源黑体）

### 3. 调整字体大小

- **中文字体大小**：滑块范围 100-300px，默认 163px
- **英文字体大小**：滑块范围 30-100px，默认 50px

### 4. 保存配置

点击 **保存配置** 按钮，配置会持久化到 `/config/webhook_config.json`

### 5. 生成封面测试

选择媒体库，配置标题，点击 **生成预览** 查看效果。

## Docker 挂载配置

确保 `docker-compose.yml` 中正确挂载了 config 目录：

```yaml
volumes:
  - /path/to/new-emby-stats/config:/config
```

容器内路径为 `/config/fonts/`，所以配置时使用 `/config/fonts/你的字体.ttf`

## 字体文件推荐

### 中文字体
- 思源黑体（Noto Sans CJK / Source Han Sans）
- 思源宋体（Noto Serif CJK / Source Han Serif）
- 阿里巴巴普惠体
- 站酷字体系列

### 英文字体
- Montserrat
- Roboto
- Open Sans
- Bebas Neue

## 注意事项

1. 字体文件大小通常在几MB到几十MB，建议选择合适的字重
2. 中文字体文件通常比英文字体大得多
3. 配置路径必须是容器内路径，即 `/config/fonts/` 开头
4. 字体文件必须有读取权限
5. 动图和静图使用相同的字体配置

## 故障排除

### 字体不生效
- 检查字体文件路径是否正确
- 确认字体文件格式是否支持（ttf/otf/woff/woff2）
- 查看后端日志，搜索 "字体" 关键字查看加载情况

### 字体路径错误
- 容器内路径为 `/config/fonts/`，不是宿主机路径
- 检查 Docker volume 挂载是否正确

### 字体显示异常
- 尝试调整字体大小
- 确认字体文件没有损坏
- 查看生成日志中的警告信息
