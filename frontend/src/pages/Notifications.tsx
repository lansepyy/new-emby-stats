import { useState, useEffect } from 'react'
import { Card } from '@/components/ui'
import { Settings, Bell, MessageSquare, Film, Save, TestTube } from 'lucide-react'

export function Notifications() {
  const [activeSection, setActiveSection] = useState<'telegram' | 'wecom' | 'discord' | 'tmdb'>('telegram')
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isTesting, setIsTesting] = useState(false)
  const [testMessage, setTestMessage] = useState('')

  // Telegram配置
  const [telegramConfig, setTelegramConfig] = useState({
    botToken: '',
    admins: '',
    users: '',
  })

  // 企业微信配置
  const [wecomConfig, setWecomConfig] = useState({
    corpId: '',
    secret: '',
    agentId: '',
    proxyUrl: 'https://qyapi.weixin.qq.com',
    toUser: '@all',
  })

  // Discord配置
  const [discordConfig, setDiscordConfig] = useState({
    webhookUrl: '',
    username: 'Emby通知',
    avatarUrl: '',
  })

  // TMDB配置
  const [tmdbConfig, setTmdbConfig] = useState({
    apiKey: '',
    imageBaseUrl: 'https://image.tmdb.org/t/p/original',
  })

  // 加载配置
  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/config/notification')
      const data = await response.json()
      
      // 更新状态
      setTelegramConfig({
        botToken: data.telegram.bot_token || '',
        admins: data.telegram.admins?.join(',') || '',
        users: data.telegram.users?.join(',') || '',
      })
      
      setWecomConfig({
        corpId: data.wecom.corp_id || '',
        secret: data.wecom.secret || '',
        agentId: data.wecom.agent_id || '',
        proxyUrl: data.wecom.proxy_url || 'https://qyapi.weixin.qq.com',
        toUser: data.wecom.to_user || '@all',
      })
      
      setDiscordConfig({
        webhookUrl: data.discord.webhook_url || '',
        username: data.discord.username || 'Emby通知',
        avatarUrl: data.discord.avatar_url || '',
      })
      
      setTmdbConfig({
        apiKey: data.tmdb.api_key || '',
        imageBaseUrl: data.tmdb.image_base_url || 'https://image.tmdb.org/t/p/original',
      })
    } catch (error) {
      console.error('加载配置失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const config = {
        telegram: {
          bot_token: telegramConfig.botToken,
          admins: telegramConfig.admins ? telegramConfig.admins.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)) : [],
          users: telegramConfig.users ? telegramConfig.users.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)) : [],
        },
        wecom: {
          corp_id: wecomConfig.corpId,
          secret: wecomConfig.secret,
          agent_id: wecomConfig.agentId,
          proxy_url: wecomConfig.proxyUrl,
          to_user: wecomConfig.toUser,
        },
        discord: {
          webhook_url: discordConfig.webhookUrl,
          username: discordConfig.username,
          avatar_url: discordConfig.avatarUrl,
        },
        tmdb: {
          api_key: tmdbConfig.apiKey,
          image_base_url: tmdbConfig.imageBaseUrl,
        }
      }
      
      const response = await fetch('/api/config/notification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      
      const result = await response.json()
      alert(result.message || '配置已保存')
    } catch (error) {
      alert('保存失败：' + (error as Error).message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleTest = async () => {
    setIsTesting(true)
    setTestMessage('')
    try {
      await fetch('/api/webhook/test')
      setTestMessage('✅ 测试通知已发送！请检查您的接收端。')
    } catch (error) {
      setTestMessage('❌ 发送失败：' + (error as Error).message)
    } finally {
      setIsTesting(false)
    }
  }

  const sections = [
    { id: 'telegram', label: 'Telegram', icon: MessageSquare },
    { id: 'wecom', label: '企业微信', icon: Bell },
    { id: 'discord', label: 'Discord', icon: MessageSquare },
    { id: 'tmdb', label: 'TMDB', icon: Film },
  ] as const

  // 加载中
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-text-secondary">加载配置中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="w-6 h-6" />
            通知配置
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            配置 Emby Webhook 通知推送服务
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleTest}
            disabled={isTesting}
            className="px-4 py-2 bg-warning text-white rounded-lg hover:bg-warning/90 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <TestTube className="w-4 h-4" />
            {isTesting ? '发送中...' : '测试通知'}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {isSaving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </div>

      {testMessage && (
        <div className={`p-4 rounded-lg ${testMessage.startsWith('✅') ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
          {testMessage}
        </div>
      )}

      {/* Configuration Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Section Tabs */}
        <Card className="p-4 h-fit">
          <div className="space-y-2">
            {sections.map(section => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeSection === section.id
                    ? 'bg-primary text-white'
                    : 'hover:bg-surface-hover'
                }`}
              >
                <section.icon className="w-5 h-5" />
                <span className="font-medium">{section.label}</span>
              </button>
            ))}
          </div>
        </Card>

        {/* Configuration Content */}
        <Card className="p-6 lg:col-span-3">
          {activeSection === 'telegram' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Telegram 配置</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">Bot Token</label>
                <input
                  type="text"
                  value={telegramConfig.botToken}
                  onChange={e => setTelegramConfig({ ...telegramConfig, botToken: e.target.value })}
                  placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-text-secondary mt-1">
                  从 @BotFather 获取的 Bot Token
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">管理员 Chat IDs</label>
                <input
                  type="text"
                  value={telegramConfig.admins}
                  onChange={e => setTelegramConfig({ ...telegramConfig, admins: e.target.value })}
                  placeholder="123456789,987654321"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-text-secondary mt-1">
                  多个 ID 用逗号分隔
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">普通用户 Chat IDs（可选）</label>
                <input
                  type="text"
                  value={telegramConfig.users}
                  onChange={e => setTelegramConfig({ ...telegramConfig, users: e.target.value })}
                  placeholder="111222333,444555666"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          {activeSection === 'wecom' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">企业微信配置</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">企业 ID (Corp ID)</label>
                <input
                  type="text"
                  value={wecomConfig.corpId}
                  onChange={e => setWecomConfig({ ...wecomConfig, corpId: e.target.value })}
                  placeholder="ww1234567890abcdef"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">应用 Secret</label>
                <input
                  type="password"
                  value={wecomConfig.secret}
                  onChange={e => setWecomConfig({ ...wecomConfig, secret: e.target.value })}
                  placeholder="应用的 Secret"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">应用 Agent ID</label>
                <input
                  type="text"
                  value={wecomConfig.agentId}
                  onChange={e => setWecomConfig({ ...wecomConfig, agentId: e.target.value })}
                  placeholder="1000002"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">API 代理地址（可选）</label>
                <input
                  type="text"
                  value={wecomConfig.proxyUrl}
                  onChange={e => setWecomConfig({ ...wecomConfig, proxyUrl: e.target.value })}
                  placeholder="https://qyapi.weixin.qq.com"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">接收用户</label>
                <input
                  type="text"
                  value={wecomConfig.toUser}
                  onChange={e => setWecomConfig({ ...wecomConfig, toUser: e.target.value })}
                  placeholder="@all 或 UserID1|UserID2"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-text-secondary mt-1">
                  @all 表示发送给所有人
                </p>
              </div>
            </div>
          )}

          {activeSection === 'discord' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Discord 配置</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">Webhook URL</label>
                <input
                  type="text"
                  value={discordConfig.webhookUrl}
                  onChange={e => setDiscordConfig({ ...discordConfig, webhookUrl: e.target.value })}
                  placeholder="https://discord.com/api/webhooks/..."
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">用户名（可选）</label>
                <input
                  type="text"
                  value={discordConfig.username}
                  onChange={e => setDiscordConfig({ ...discordConfig, username: e.target.value })}
                  placeholder="Emby通知"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">头像 URL（可选）</label>
                <input
                  type="text"
                  value={discordConfig.avatarUrl}
                  onChange={e => setDiscordConfig({ ...discordConfig, avatarUrl: e.target.value })}
                  placeholder="https://example.com/avatar.png"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}

          {activeSection === 'tmdb' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">TMDB 配置</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <input
                  type="password"
                  value={tmdbConfig.apiKey}
                  onChange={e => setTmdbConfig({ ...tmdbConfig, apiKey: e.target.value })}
                  placeholder="your_tmdb_api_key"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-text-secondary mt-1">
                  从 <a href="https://www.themoviedb.org/settings/api" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">TMDB API 设置</a> 获取
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">图片基础 URL</label>
                <input
                  type="text"
                  value={tmdbConfig.imageBaseUrl}
                  onChange={e => setTmdbConfig({ ...tmdbConfig, imageBaseUrl: e.target.value })}
                  placeholder="https://image.tmdb.org/t/p/original"
                  className="w-full px-4 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="mt-6 p-4 bg-surface-hover rounded-lg">
                <h4 className="font-medium mb-2">关于 TMDB</h4>
                <p className="text-sm text-text-secondary">
                  TMDB (The Movie Database) 用于获取电影和剧集的高质量海报、背景图和详细信息。
                  配置后，通知中将显示更精美的媒体图片。
                </p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Webhook URL Info */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Emby Webhook 设置</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Webhook URL</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={`${window.location.origin}/api/webhook/emby`}
                readOnly
                className="flex-1 px-4 py-2 bg-surface border border-border rounded-lg"
              />
              <button
                onClick={() => {
                  navigator.clipboard.writeText(`${window.location.origin}/api/webhook/emby`)
                  alert('已复制到剪贴板')
                }}
                className="px-4 py-2 bg-surface-hover rounded-lg hover:bg-surface transition-colors"
              >
                复制
              </button>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              在 Emby 服务器的 Webhook 插件中配置此 URL，即可接收播放、入库、登录等事件通知
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
