# 通知模板功能说明

## 功能概述

新版本新增了完整的通知模板管理功能，支持创建自定义通知模板并通过企业微信机器人发送消息。

## 主要特性

### 🔔 通知模板管理
- **创建模板**: 支持自定义模板名称、内容和变量
- **模板变量**: 使用 `{变量名}` 格式定义动态内容
- **模板渲染**: 实时预览模板渲染效果
- **默认模板**: 内置常用模板，可一键创建

### 💼 企业微信集成
- **多配置管理**: 支持配置多个企业微信机器人
- **连接测试**: 一键测试WebHook URL有效性
- **发送统计**: 实时统计发送成功率和日志
- **状态管理**: 支持启用/禁用配置

### 📊 统计分析
- **发送统计**: 显示总配置数、发送次数、成功率等
- **详细日志**: 记录每次发送的状态、错误信息和时间
- **可视图表**: 直观显示通知发送情况

## 使用方法

### 1. 访问通知功能

**方式一**: 点击顶部菜单栏的铃铛图标 🔔

**方式二**: 在底部导航栏选择"通知"标签页

### 2. 企业微信配置

1. 点击铃铛图标进入管理面板
2. 切换到"企业微信配置"标签页
3. 点击"新建配置"按钮
4. 填写配置信息：
   - **配置名称**: 为配置起一个有意义的名称
   - **WebHook URL**: 企业微信机器人的WebHook地址
   - **启用状态**: 勾选启用此配置
5. 点击"保存"完成配置
6. 使用测试功能验证配置有效性

### 3. 创建通知模板

1. 在通知模板面板中切换到"模板管理"标签页
2. 点击"新建模板"按钮
3. 填写模板信息：
   - **模板名称**: 模板的显示名称
   - **模板内容**: 消息内容，支持变量占位符
4. 使用 `{变量名}` 格式定义变量，例如：
   ```
   📊 Emby 播放统计报告
   
   👤 用户: {username}
   🎬 观看内容: {content_title}
   ⏱️ 播放时长: {duration}
   
   📈 详细数据请查看 Emby Stats
   ```
5. 点击"保存"完成模板创建
6. 或者点击"创建默认模板"快速添加常用模板

### 4. 发送通知

1. 切换到"发送通知"标签页
2. 选择企业微信配置
3. 选择通知模板
4. 填写模板变量对应的值
5. 预览生成的完整消息
6. 点击"发送通知"

## API 接口

### 通知模板管理

```bash
# 获取所有模板
GET /api/notification-templates/

# 创建模板
POST /api/notification-templates/

# 更新模板
PUT /api/notification-templates/{template_id}

# 删除模板
DELETE /api/notification-templates/{template_id}

# 渲染模板
POST /api/notification-templates/{template_id}/render

# 创建默认模板
POST /api/notification-templates/create-defaults
```

### 企业微信管理

```bash
# 获取所有配置
GET /api/wecom/configs

# 创建配置
POST /api/wecom/configs

# 更新配置
PUT /api/wecom/configs/{config_id}

# 删除配置
DELETE /api/wecom/configs/{config_id}

# 测试连接
POST /api/wecom/test

# 发送通知
POST /api/wecom/send

# 获取日志
GET /api/wecom/logs

# 获取统计
GET /api/wecom/statistics
```

## 数据库表结构

### notification_templates
- `id`: 模板ID
- `name`: 模板名称
- `channel`: 通知渠道（目前支持 wecom）
- `template_content`: 模板内容
- `variables`: 变量列表（JSON格式）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### wecom_configs
- `id`: 配置ID
- `name`: 配置名称
- `webhook_url`: WebHook地址
- `enabled`: 是否启用
- `created_at`: 创建时间
- `updated_at`: 更新时间

### wecom_logs
- `id`: 日志ID
- `config_id`: 配置ID（外键）
- `template_id`: 模板ID（外键，可选）
- `message_content`: 发送的消息内容
- `status`: 发送状态（success/failed）
- `error_message`: 错误信息
- `sent_at`: 发送时间

## 默认模板

系统提供以下默认模板：

1. **日常播放统计**
   - 用途：定期发送Emby播放统计报告
   - 变量：`date_range`, `total_plays`, `total_duration`, `active_users`, `top_content`

2. **用户活动提醒**
   - 用途：提醒特定用户的观看活动
   - 变量：`username`, `content_title`, `duration`, `device`, `watch_time`

3. **新用户注册通知**
   - 用途：新用户注册时的欢迎消息
   - 变量：`username`, `email`, `device`, `register_time`

## 最佳实践

### 1. 模板设计
- 使用表情符号增加可读性
- 合理设置变量，提高模板复用性
- 保持内容简洁明了

### 2. 配置管理
- 为不同用途创建不同的配置
- 定期测试配置的连通性
- 合理命名配置便于管理

### 3. 变量命名
- 使用有意义的变量名，如 `user_name` 而非 `a`
- 保持变量命名风格一致
- 避免特殊字符和空格

### 4. 消息发送
- 发送前务必预览消息内容
- 测试变量渲染效果
- 关注发送日志及时发现问题

## 故障排除

### 常见问题

1. **企业微信消息发送失败**
   - 检查WebHook URL是否正确
   - 确认企业微信机器人未停用
   - 查看详细错误日志

2. **模板变量未正确渲染**
   - 检查变量名是否匹配（区分大小写）
   - 确认变量在上下文中提供了值
   - 验证模板语法是否正确

3. **配置无法保存**
   - 检查必填字段是否完整
   - 确认数据库连接正常
   - 查看后端服务日志

### 调试方法

1. **使用测试功能**
   - 在配置管理中使用"测试连接"
   - 发送测试消息验证功能

2. **查看日志**
   - 访问通知页面的"发送日志"
   - 查看详细的发送状态和错误信息

3. **检查配置**
   - 确认所有必需字段都已填写
   - 验证配置处于启用状态

## 更新日志

### v1.86
- ✨ 新增通知模板管理功能
- ✨ 新增企业微信机器人集成
- ✨ 新增模板渲染和实时预览
- ✨ 新增发送统计和日志功能
- ✨ 新增默认模板库
- 🎨 新增通知管理界面
- 📱 新增通知页面展示统计信息