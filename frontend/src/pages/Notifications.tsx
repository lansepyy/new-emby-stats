import { useState, useEffect } from 'react'
import { Card } from '@/components/ui'
import { Settings, Bell, MessageSquare, Film, Save, TestTube, Eye, X } from 'lucide-react'
import html2canvas from 'html2canvas'
import { ReportImage } from '@/components/ReportImage'

export function Notifications() {
  const [activeSection, setActiveSection] = useState<'telegram' | 'wecom' | 'discord' | 'tmdb' | 'report'>('telegram')
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isTesting, setIsTesting] = useState(false)
  const [testMessage, setTestMessage] = useState('')
  const [isSendingReport, setIsSendingReport] = useState(false)
  const [reportMessage, setReportMessage] = useState('')
  
  // 报告预览
  const [showPreview, setShowPreview] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [previewType, setPreviewType] = useState<'daily' | 'weekly' | 'monthly'>('daily')

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

  // 报告推送配置
  const [reportConfig, setReportConfig] = useState({
    enabled: false,
    dailyEnabled: false,
    weeklyEnabled: false,
    monthlyEnabled: false,
    dailyTime: '21:00',
    weeklyTime: '21:00',
    weeklyDay: '0', // 0=周日
    monthlyTime: '21:00',
    monthlyDay: '1', // 1-28
    channels: {
      telegram: true,
      wecom: false,
      discord: false,
    }
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
      
      setReportConfig({
        enabled: data.report?.enabled || false,
        dailyEnabled: data.report?.daily_enabled || false,
        weeklyEnabled: data.report?.weekly_enabled || false,
        monthlyEnabled: data.report?.monthly_enabled || false,
        dailyTime: data.report?.daily_time || '21:00',
        weeklyTime: data.report?.weekly_time || '21:00',
        weeklyDay: String(data.report?.weekly_day || '0'),
        monthlyTime: data.report?.monthly_time || '21:00',
        monthlyDay: String(data.report?.monthly_day || '1'),
        channels: {
          telegram: data.report?.channels?.telegram !== false,
          wecom: data.report?.channels?.wecom || false,
          discord: data.report?.channels?.discord || false,
        }
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
        },
        report: {
          enabled: reportConfig.enabled,
          daily_enabled: reportConfig.dailyEnabled,
          weekly_enabled: reportConfig.weeklyEnabled,
          monthly_enabled: reportConfig.monthlyEnabled,
          daily_time: reportConfig.dailyTime,
          weekly_time: reportConfig.weeklyTime,
          weekly_day: parseInt(reportConfig.weeklyDay),
          monthly_time: reportConfig.monthlyTime,
          monthly_day: parseInt(reportConfig.monthlyDay),
          channels: reportConfig.channels,
        }      }
      
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

  const handleSendReport = async (type: 'daily' | 'weekly' | 'monthly') => {
    setIsSendingReport(true)
    setReportMessage('')
    try {
      // 1. 获取报告数据
      const reportResponse = await fetch(`/api/report/generate?type=${type}`)
      if (!reportResponse.ok) throw new Error('获取报告数据失败')
      const reportData = await reportResponse.json()

      // 2. 获取封面图片
      const coverImages: Record<string, string> = {}
      for (const item of reportData.top_content.slice(0, 5)) {
        if (item.item_id) {
          try {
            const imgResponse = await fetch(`/api/poster/${item.item_id}?maxHeight=120&maxWidth=90`)
            if (imgResponse.ok) {
              const blob = await imgResponse.blob()
              coverImages[item.item_id] = URL.createObjectURL(blob)
            }
          } catch (e) {
            console.warn(`封面获取失败: ${item.name}`, e)
          }
        }
      }

      // 3. 渲染报告组件并生成图片
      const reportElement = document.createElement('div')
      reportElement.style.position = 'absolute'
      reportElement.style.left = '-9999px'
      document.body.appendChild(reportElement)

      const { createRoot } = await import('react-dom/client')
      const root = createRoot(reportElement)
      
      await new Promise<void>((resolve) => {
        root.render(
          <ReportImage data={reportData} coverImages={coverImages} />
        )
        setTimeout(resolve, 500) // 等待渲染完成
      })

      const canvas = await html2canvas(reportElement.querySelector('div')!, {
        backgroundColor: '#1a202c',
        scale: 2,
        logging: false,
        useCORS: true,
        onclone: (clonedDoc) => {
          // 移除所有可能使用 oklch 的样式
          const clonedElement = clonedDoc.querySelector('div')
          if (clonedElement) {
            // 强制使用内联样式替换可能的 oklch 颜色
            clonedElement.querySelectorAll('*').forEach((el) => {
              const htmlEl = el as HTMLElement
              const computedStyle = window.getComputedStyle(el)
              
              // 替换背景色
              if (computedStyle.backgroundColor && computedStyle.backgroundColor.includes('oklch')) {
                htmlEl.style.backgroundColor = computedStyle.backgroundColor
              }
              // 替换文字颜色
              if (computedStyle.color && computedStyle.color.includes('oklch')) {
                htmlEl.style.color = computedStyle.color
              }
              // 替换边框颜色
              if (computedStyle.borderColor && computedStyle.borderColor.includes('oklch')) {
                htmlEl.style.borderColor = computedStyle.borderColor
              }
            })
          }
        }
      })

      // 清理
      root.unmount()
      document.body.removeChild(reportElement)
      Object.values(coverImages).forEach(url => URL.revokeObjectURL(url))

      // 4. 转换为Blob并上传
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((b) => resolve(b!), 'image/png', 0.95)
      })

      const formData = new FormData()
      formData.append('image', blob, 'report.png')
      formData.append('type', type)

      const sendResponse = await fetch('/api/report/send-image', {
        method: 'POST',
        body: formData
      })

      if (sendResponse.ok) {
        setReportMessage(`✅ ${type === 'daily' ? '每日' : type === 'weekly' ? '每周' : '每月'}报告已发送！`)
      } else {
        setReportMessage('❌ 发送失败，请检查配置')
      }
    } catch (error) {
      setReportMessage('❌ 发送失败：' + (error as Error).message)
    } finally {
      setIsSendingReport(false)
    }
  }

  // 生成报告预览
  const handlePreviewReport = async (type: 'daily' | 'weekly' | 'monthly') => {
    setPreviewType(type)
    setShowPreview(true)
    setPreviewLoading(true)
    setPreviewImage(null)

    try {
      // 1. 获取报告数据
      const response = await fetch(`/api/report/generate?type=${type}`)
      if (!response.ok) throw new Error('获取报告数据失败')
      
      const reportData = await response.json()

      // 2. 获取封面图
      const coverImages: Record<string, string> = {}
      for (const item of reportData.top_content.slice(0, 5)) {
        if (item.item_id) {
          try {
            const imgResponse = await fetch(`/api/poster/${item.item_id}?maxHeight=155&maxWidth=110`)
            if (imgResponse.ok) {
              const blob = await imgResponse.blob()
              coverImages[item.item_id] = URL.createObjectURL(blob)
            }
          } catch (e) {
            console.warn(`封面获取失败: ${item.name}`, e)
          }
        }
      }

      // 3. 渲染报告组件并生成图片
      const reportElement = document.createElement('div')
      reportElement.style.position = 'absolute'
      reportElement.style.left = '-9999px'
      document.body.appendChild(reportElement)

      const { createRoot } = await import('react-dom/client')
      const root = createRoot(reportElement)
      
      await new Promise<void>((resolve) => {
        root.render(
          <ReportImage data={reportData} coverImages={coverImages} />
        )
        setTimeout(resolve, 500) // 等待渲染完成
      })

      const canvas = await html2canvas(reportElement.querySelector('div')!, {
        backgroundColor: '#1a202c',
        scale: 2,
        logging: false,
        useCORS: true,
      })

      // 清理
      root.unmount()
      document.body.removeChild(reportElement)
      
      // 转换为图片URL
      const imageUrl = canvas.toDataURL('image/png', 0.95)
      setPreviewImage(imageUrl)
      
      // 清理 blob URLs
      Object.values(coverImages).forEach(url => URL.revokeObjectURL(url))
    } catch (error) {
      console.error('预览失败:', error)
      alert('生成预览失败：' + (error as Error).message)
      setShowPreview(false)
    } finally {
      setPreviewLoading(false)
    }
  }

  const sections = [
    { id: 'telegram', label: 'Telegram', icon: MessageSquare },
    { id: 'wecom', label: '企业微信', icon: Bell },
    { id: 'discord', label: 'Discord', icon: MessageSquare },
    { id: 'tmdb', label: 'TMDB', icon: Film },
    { id: 'report', label: '观影报告', icon: Settings },
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

          {activeSection === 'report' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold mb-4">观影报告推送</h3>
              
              {/* 总开关 */}
              <div className="flex items-center justify-between p-4 bg-surface-hover rounded-lg">
                <div>
                  <h4 className="font-medium">启用报告推送</h4>
                  <p className="text-sm text-text-secondary">开启后将按设定的时间自动推送报告</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reportConfig.enabled}
                    onChange={e => setReportConfig({ ...reportConfig, enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>

              {/* 推送渠道选择 */}
              <div className="p-4 bg-surface-hover rounded-lg">
                <h4 className="font-medium mb-3">推送渠道</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer p-2 -m-2 rounded-lg hover:bg-content2 transition-colors">
                    <input
                      type="checkbox"
                      checked={reportConfig.channels.telegram}
                      onChange={e => setReportConfig({
                        ...reportConfig,
                        channels: { ...reportConfig.channels, telegram: e.target.checked }
                      })}
                      className="w-5 h-5 text-primary bg-surface border-border rounded focus:ring-primary cursor-pointer"
                    />
                    <span className="flex-1">Telegram</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer p-2 -m-2 rounded-lg hover:bg-content2 transition-colors">
                    <input
                      type="checkbox"
                      checked={reportConfig.channels.wecom}
                      onChange={e => setReportConfig({
                        ...reportConfig,
                        channels: { ...reportConfig.channels, wecom: e.target.checked }
                      })}
                      className="w-5 h-5 text-primary bg-surface border-border rounded focus:ring-primary cursor-pointer"
                    />
                    <span className="flex-1">企业微信</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer p-2 -m-2 rounded-lg hover:bg-content2 transition-colors">
                    <input
                      type="checkbox"
                      checked={reportConfig.channels.discord}
                      onChange={e => setReportConfig({
                        ...reportConfig,
                        channels: { ...reportConfig.channels, discord: e.target.checked }
                      })}
                      className="w-5 h-5 text-primary bg-surface border-border rounded focus:ring-primary cursor-pointer"
                    />
                    <span className="flex-1">Discord</span>
                  </label>
                </div>
              </div>

              {/* 每日报告 */}
              <div className="border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium">每日报告</h4>
                    <p className="text-sm text-text-secondary">每天推送昨日观影统计</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={reportConfig.dailyEnabled}
                      onChange={e => setReportConfig({ ...reportConfig, dailyEnabled: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
                {reportConfig.dailyEnabled && (
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2">
                      <span className="text-sm">推送时间：</span>
                      <input
                        type="time"
                        value={reportConfig.dailyTime}
                        onChange={e => setReportConfig({ ...reportConfig, dailyTime: e.target.value })}
                        className="px-3 py-1.5 bg-surface border border-border rounded-lg"
                      />
                    </label>
                    <button
                      onClick={() => handlePreviewReport('daily')}
                      disabled={previewLoading}
                      className="px-3 py-1.5 bg-surface-hover text-text-primary rounded-lg hover:bg-content2 transition-colors disabled:opacity-50 text-sm flex items-center gap-1.5"
                    >
                      <Eye className="w-4 h-4" />
                      预览
                    </button>
                    <button
                      onClick={() => handleSendReport('daily')}
                      disabled={isSendingReport}
                      className="px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 text-sm"
                    >
                      立即发送
                    </button>
                  </div>
                )}
              </div>

              {/* 每周报告 */}
              <div className="border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium">每周报告</h4>
                    <p className="text-sm text-text-secondary">每周推送本周观影统计</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={reportConfig.weeklyEnabled}
                      onChange={e => setReportConfig({ ...reportConfig, weeklyEnabled: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
                {reportConfig.weeklyEnabled && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2">
                        <span className="text-sm">推送日期：</span>
                        <select
                          value={reportConfig.weeklyDay}
                          onChange={e => setReportConfig({ ...reportConfig, weeklyDay: e.target.value })}
                          className="px-3 py-1.5 bg-surface border border-border rounded-lg"
                        >
                          <option value="0">周日</option>
                          <option value="1">周一</option>
                          <option value="2">周二</option>
                          <option value="3">周三</option>
                          <option value="4">周四</option>
                          <option value="5">周五</option>
                          <option value="6">周六</option>
                        </select>
                      </label>
                      <label className="flex items-center gap-2">
                        <span className="text-sm">时间：</span>
                        <input
                          type="time"
                          value={reportConfig.weeklyTime}
                          onChange={e => setReportConfig({ ...reportConfig, weeklyTime: e.target.value })}
                          className="px-3 py-1.5 bg-surface border border-border rounded-lg"
                        />
                      </label>
                      <button
                        onClick={() => handlePreviewReport('weekly')}
                        disabled={previewLoading}
                        className="px-3 py-1.5 bg-surface-hover text-text-primary rounded-lg hover:bg-content2 transition-colors disabled:opacity-50 text-sm flex items-center gap-1.5"
                      >
                        <Eye className="w-4 h-4" />
                        预览
                      </button>
                      <button
                        onClick={() => handleSendReport('weekly')}
                        disabled={isSendingReport}
                        className="px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 text-sm"
                      >
                        立即发送
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* 每月报告 */}
              <div className="border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium">每月报告</h4>
                    <p className="text-sm text-text-secondary">每月推送本月观影统计</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={reportConfig.monthlyEnabled}
                      onChange={e => setReportConfig({ ...reportConfig, monthlyEnabled: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
                {reportConfig.monthlyEnabled && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-2">
                        <span className="text-sm">推送日期：每月</span>
                        <select
                          value={reportConfig.monthlyDay}
                          onChange={e => setReportConfig({ ...reportConfig, monthlyDay: e.target.value })}
                          className="px-3 py-1.5 bg-surface border border-border rounded-lg"
                        >
                          {Array.from({ length: 28 }, (_, i) => i + 1).map(day => (
                            <option key={day} value={day}>{day}日</option>
                          ))}
                        </select>
                      </label>
                      <label className="flex items-center gap-2">
                        <span className="text-sm">时间：</span>
                        <input
                          type="time"
                          value={reportConfig.monthlyTime}
                          onChange={e => setReportConfig({ ...reportConfig, monthlyTime: e.target.value })}
                          className="px-3 py-1.5 bg-surface border border-border rounded-lg"
                        />
                      </label>
                      <button
                        onClick={() => handlePreviewReport('monthly')}
                        disabled={previewLoading}
                        className="px-3 py-1.5 bg-surface-hover text-text-primary rounded-lg hover:bg-content2 transition-colors disabled:opacity-50 text-sm flex items-center gap-1.5"
                      >
                        <Eye className="w-4 h-4" />
                        预览
                      </button>
                      <button
                        onClick={() => handleSendReport('monthly')}
                        disabled={isSendingReport}
                        className="px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 text-sm"
                      >
                        立即发送
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* 报告发送提示 */}
              {reportMessage && (
                <div className={`p-4 rounded-lg ${reportMessage.startsWith('✅') ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                  {reportMessage}
                </div>
              )}

              {/* 说明 */}
              <div className="mt-6 p-4 bg-surface-hover rounded-lg">
                <h4 className="font-medium mb-2">关于观影报告</h4>
                <ul className="text-sm text-text-secondary space-y-1 list-disc list-inside">
                  <li>报告会发送到已配置的推送渠道（Telegram/企业微信/Discord）</li>
                  <li>每日报告统计昨天的观影数据</li>
                  <li>每周报告统计过去7天的数据</li>
                  <li>每月报告统计过去30天的数据</li>
                  <li>点击"立即发送"可以手动测试报告推送</li>
                </ul>
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

      {/* 报告预览弹窗 */}
      {showPreview && (
      <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setShowPreview(false)}>
        <div className="bg-surface rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
          {/* 头部 */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h2 className="text-xl font-bold">
                {previewType === 'daily' ? '每日' : previewType === 'weekly' ? '每周' : '每月'}报告预览
              </h2>
              <p className="text-sm text-text-secondary mt-1">
                这是将要发送的报告效果
              </p>
            </div>
            <button
              onClick={() => setShowPreview(false)}
              className="p-2 hover:bg-surface-hover rounded-lg transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* 内容 */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            {previewLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-text-secondary">正在生成预览...</p>
              </div>
            ) : previewImage ? (
              <div className="flex justify-center">
                <img 
                  src={previewImage} 
                  alt="报告预览" 
                  className="max-w-full h-auto rounded-lg shadow-lg"
                  style={{ maxHeight: 'calc(90vh - 240px)' }}
                />
              </div>
            ) : (
              <div className="text-center py-16 text-text-secondary">
                预览生成失败
              </div>
            )}
          </div>

          {/* 底部 */}
          <div className="flex items-center justify-between p-6 border-t border-border bg-surface-hover">
            <p className="text-sm text-text-secondary">
              💡 实际发送的报告可能因推送渠道而略有差异
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 bg-surface-hover hover:bg-content2 rounded-lg transition-colors"
              >
                关闭
              </button>
              <button
                onClick={() => {
                  setShowPreview(false)
                  handleSendReport(previewType)
                }}
                disabled={isSendingReport}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                发送此报告
              </button>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  )
}
