# 报告图片资源目录

此目录用于存放报告图片生成所需的资源文件。

## 目录结构

```
res/
├── bg/                    # 背景图片目录（可选）
│   ├── bg1.jpg
│   ├── bg2.png
│   └── ...
├── PingFang Bold.ttf     # 中文字体（可选）
└── README.md
```

## 资源说明

### 背景图片 (bg/)

可以放置精美的背景图片，系统会随机选择一张作为报告背景。

- **支持格式**: JPG, PNG
- **建议尺寸**: 宽度至少 1080px，高度 1500px 以上
- **效果**: 系统会自动调整大小、裁剪，并添加半透明遮罩以保证文字清晰

如果不提供背景图片，系统会使用纯色背景。

### 字体文件

可以放置 `.ttf` 或 `.ttc` 格式的中文字体文件。

- **推荐字体**: 
  - PingFang Bold.ttf (苹方粗体)
  - Microsoft YaHei Bold.ttc (微软雅黑粗体)
  - SourceHanSansCN-Bold.otf (思源黑体粗体)

- **命名建议**: 文件名包含 `bold` 的会被优先用于粗体文字

如果不提供字体文件，系统会尝试使用系统字体。

## 如何获取 MP 插件资源

如果你想使用与 MP 插件相同的美观效果，可以：

1. 从 MP 插件的 `res` 目录复制背景图片到此目录的 `bg/` 文件夹
2. 复制 `PingFang Bold.ttf` 字体文件到此目录

## 示例

```bash
# 创建背景图片目录
mkdir -p res/bg

# 复制背景图片（示例）
cp /path/to/mp/res/bg/*.jpg res/bg/
cp /path/to/mp/res/bg/*.png res/bg/

# 复制字体文件（示例）
cp /path/to/mp/res/PingFang\ Bold.ttf res/
```
