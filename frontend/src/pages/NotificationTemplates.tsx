import { useState, useEffect } from 'react'
import { Card } from '@/components/ui'
import { FileCode, Save, RotateCcw } from 'lucide-react'

const DEFAULT_TEMPLATES = {
  default: {
    title: "{% if action == '新入库' and media_type == '电影' %}🎬 {% elif action == '新入库' and media_type == '剧集' %}📺 {% elif action == '新入库' and media_type == '有声书' %}📚 {% elif action == '新入库' %}🆕 {% elif action == '测试' %}🧪 {% elif action == '开始播放' %}▶️ {% elif action == '停止播放' %}⏹️ {% elif action == '登录成功' %}✅ {% elif action == '登录失败' %}❌ {% elif action == '标记了' %}🏷️ {% endif %}{% if user_name %}【{{ user_name }}】{% endif %}{{ action }}{% if media_type %} {{ media_type }} {% endif %}{{ item_name }}",
    text: "{% if rating %}⭐ 评分：{{ rating }}/10\n{% endif %}📚 类型：{{ media_type }}\n{% if progress %}🔄 进度：{{ progress }}%\n{% endif %}{% if ip_address %}🌐 IP地址：{{ ip_address }}\n{% endif %}{% if device_name %}📱 设备：{{ client }} {{ device_name }}\n{% endif %}{% if size %}💾 大小：{{ size }}\n{% endif %}{% if tmdb_id %}🎬 TMDB ID：{{ tmdb_id }}\n{% endif %}{% if imdb_id %}🎞️ IMDB ID：{{ imdb_id }}\n{% endif %}🕒 时间：{{ now_time }}\n{% if overview %}\n📝 剧情：{{ overview }}{% endif %}"
  },
  playback: {
    title: "{% if action == '开始播放' %}▶️ {{ action }} {{ media_type }}：{{ item_name }}{% if item_year %}（{{ item_year }}）{% endif %}{% endif %}{% if action == '停止播放' %}⏹️ {{ action }} {{ media_type }}：{{ item_name }}{% if item_year %}（{{ item_year }}）{% endif %}{% endif %}{% if action == '暂停播放' %}⏸️ {{ action }} {{ media_type }}：{{ item_name }}{% if item_year %}（{{ item_year }}）{% endif %}{% endif %}",
    text: "{% if media_type == '电影' %}🎬 类型：电影{% elif media_type == '电视剧' %}📺 类型：电视剧{% else %}🎥 类型：{{ media_type }}{% endif %}\n{% if rating %}🌟 评分：{{ rating }}/10\n{% endif %}🙋 用户：{{ user_name }}\n📱 设备：{{ device_name }}\n🌐 IP：{{ ip_address }}\n{% if progress %}🔄 进度：{{ progress }}%\n{% endif %}🕒 时间：{{ now_time }}\n{% if overview %}📜 剧情：{{ overview }}{% endif %}"
  },
  library: {
    title: "{% if media_type == '电影' %}🎬{% elif media_type == '剧集' %}📺{% else %}🆕{% endif %} 新入库 {{ media_type }}：{{ item_name }}",
    text: "{% if media_type == '电影' %}🎬 类型：电影{% elif media_type == '剧集' %}📺 类型：剧集{% else %}🆕 类型：{{ media_type }}{% endif %}\n{% if rating %}⭐ 评分：{{ rating }}/10\n{% endif %}{% if item_year %}📅 年份：{{ item_year }}\n{% endif %}{% if size %}💾 大小：{{ size }}\n{% endif %}🕒 时间：{{ now_time }}\n{% if overview %}📝 简介：{{ overview }}{% endif %}"
  },
  login: {
    title: "{% if action == '登录成功' %}🔑 登录成功 ✅{% elif action == '登录失败' %}🔓 登录失败 ❌{% else %}🚪 用户登录通知{% endif %}",
    text: "🙋 用户：{{ user_name }}\n💻 平台：{{ client }}\n📱 设备：{{ device_name }}\n🌍 IP地址：{{ ip_address }}\n🕒 登录时间：{{ now_time }}"
  },
  mark: {
    title: "🏷️ {{ user_name }} {{ action }} {{ media_type }}：{{ item_name }}",
    text: "{% if rating %}⭐ 评分：{{ rating }}\n{% endif %}📺 类型：{{ media_type }}\n🕒 时间：{{ now_time }}\n{% if overview %}📝 简介：{{ overview }}{% endif %}"
  }
}

interface NotificationTemplatesProps {
  onBack?: () => void
}

export function NotificationTemplates({ onBack }: NotificationTemplatesProps) {
  const [templates, setTemplates] = useState(DEFAULT_TEMPLATES)
  const [activeTemplate, setActiveTemplate] = useState<keyof typeof DEFAULT_TEMPLATES>('default')
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // 加载模板
  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/config/notification/templates')
      const data = await response.json()
      if (data.templates) {
        setTemplates(data.templates)
      }
    } catch (error) {
      console.error('加载模板失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const response = await fetch('/api/config/notification/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ templates })
      })
      const result = await response.json()
      alert(result.message || '模板已保存')
    } catch (error) {
      alert('保存失败：' + (error as Error).message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    if (confirm('确定要重置为默认模板吗？此操作不可恢复。')) {
      setTemplates(DEFAULT_TEMPLATES)
    }
  }

  // 格式化当前模板：移除每行前面的空格
  const handleFormat = () => {
    const formatted = {
      title: templates[activeTemplate].title.split('\n').map(line => line.trim()).join('\n'),
      text: templates[activeTemplate].text.split('\n').map(line => line.trim()).join('\n')
    }
    setTemplates({
      ...templates,
      [activeTemplate]: formatted
    })
  }

  const templateTypes = [
    { id: 'default', label: '默认模板', desc: '通用事件通知' },
    { id: 'playback', label: '播放模板', desc: '播放、暂停、停止事件' },
    { id: 'library', label: '入库模板', desc: '媒体新入库事件' },
    { id: 'login', label: '登录模板', desc: '用户登录事件' },
    { id: 'mark', label: '标记模板', desc: '标记、评分事件' },
  ] as const

  // 加载中
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-text-secondary">加载模板中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          {onBack && (
            <button
              onClick={onBack}
              className="text-primary hover:underline mb-2"
            >
              ← 返回通知配置
            </button>
          )}
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <FileCode className="w-6 h-6" />
            通知模板管理
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            使用 Jinja2 模板语法自定义通知内容
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-surface-hover rounded-lg hover:bg-surface transition-colors flex items-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            重置默认
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {isSaving ? '保存中...' : '保存模板'}
          </button>
        </div>
      </div>

      {/* Template Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Template List */}
        <Card className="p-4 h-fit">
          <h3 className="font-semibold mb-3">模板类型</h3>
          <div className="space-y-2">
            {templateTypes.map(type => (
              <button
                key={type.id}
                onClick={() => setActiveTemplate(type.id)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  activeTemplate === type.id
                    ? 'bg-primary text-white'
                    : 'hover:bg-surface-hover'
                }`}
              >
                <div className="font-medium">{type.label}</div>
                <div className={`text-xs mt-1 ${activeTemplate === type.id ? 'text-white/80' : 'text-text-secondary'}`}>
                  {type.desc}
                </div>
              </button>
            ))}
          </div>
        </Card>

        {/* Template Editor */}
        <Card className="p-6 lg:col-span-3">
          <h3 className="text-lg font-semibold mb-4">
            {templateTypes.find(t => t.id === activeTemplate)?.label}
          </h3>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium">标题模板</label>
                <button
                  onClick={handleFormat}
                  className="text-xs text-primary hover:underline"
                >
                  格式化（移除空格）
                </button>
              </div>
              <textarea
                value={templates[activeTemplate].title}
                onChange={e => setTemplates({
                  ...templates,
                  [activeTemplate]: { ...templates[activeTemplate], title: e.target.value }
                })}
                rows={3}
                className="w-full px-2 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                style={{ whiteSpace: 'pre', overflowWrap: 'normal', overflowX: 'auto' }}
                placeholder="输入标题模板..."
                spellCheck={false}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">内容模板</label>
              <textarea
                value={templates[activeTemplate].text}
                onChange={e => setTemplates({
                  ...templates,
                  [activeTemplate]: { ...templates[activeTemplate], text: e.target.value }
                })}
                rows={12}
                className="w-full px-2 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                style={{ whiteSpace: 'pre', overflowWrap: 'normal', overflowX: 'auto' }}
                placeholder="输入内容模板..."
                spellCheck={false}
              />
            </div>
          </div>

          {/* Template Variables Reference */}
          <div className="mt-6 p-4 bg-surface-hover rounded-lg">
            <h4 className="font-medium mb-3">可用变量</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <code className="text-primary">{'{{ action }}'}</code> - 动作
              </div>
              <div>
                <code className="text-primary">{'{{ user_name }}'}</code> - 用户名
              </div>
              <div>
                <code className="text-primary">{'{{ media_type }}'}</code> - 媒体类型
              </div>
              <div>
                <code className="text-primary">{'{{ item_name }}'}</code> - 媒体名称
              </div>
              <div>
                <code className="text-primary">{'{{ item_year }}'}</code> - 年份
              </div>
              <div>
                <code className="text-primary">{'{{ rating }}'}</code> - 评分
              </div>
              <div>
                <code className="text-primary">{'{{ progress }}'}</code> - 播放进度
              </div>
              <div>
                <code className="text-primary">{'{{ device_name }}'}</code> - 设备名
              </div>
              <div>
                <code className="text-primary">{'{{ ip_address }}'}</code> - IP地址
              </div>
              <div>
                <code className="text-primary">{'{{ now_time }}'}</code> - 时间
              </div>
              <div>
                <code className="text-primary">{'{{ overview }}'}</code> - 简介
              </div>
              <div>
                <code className="text-primary">{'{{ tmdb_id }}'}</code> - TMDB ID
              </div>
            </div>
            <div className="mt-3 text-xs text-text-secondary">
              <p>💡 提示：使用 Jinja2 语法，如 <code className="text-primary">{'{% if condition %}'}</code> ... <code className="text-primary">{'{% endif %}'}</code></p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
