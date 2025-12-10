import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Bell, Settings, FileText, Send, RefreshCw, AlertCircle, CheckCircle, Clock,
  Copy, Eye, EyeOff, AlertTriangle, Loader2, Save, X
} from 'lucide-react'
import { api } from '@/services/api'
import type { NotificationsData, EmbyChannelConfig, TelegramChannelConfig, DiscordChannelConfig, WeComChannelConfig, TMDBChannelConfig } from '@/types'

interface LoadingState {
  isLoading: boolean
  error: string | null
}

interface FormState {
  emby: EmbyChannelConfig
  telegram: TelegramChannelConfig
  discord: DiscordChannelConfig
  wecom: WeComChannelConfig
  tmdb: TMDBChannelConfig
}

interface ValidationErrors {
  [key: string]: string
}

interface FormFeedback {
  message: string
  type: 'success' | 'error'
}

export function Notifications() {
  const [data, setData] = useState<NotificationsData | null>(null)
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    error: null
  })
  const [activeSection, setActiveSection] = useState<'settings' | 'templates' | 'preview' | 'history'>('settings')
  const [formState, setFormState] = useState<FormState>({
    emby: { enabled: false },
    telegram: { enabled: false, admin_users: [], regular_users: [] },
    discord: { enabled: false },
    wecom: { enabled: false, user_list: [] },
    tmdb: { enabled: false }
  })
  const [originalFormState, setOriginalFormState] = useState<FormState>(formState)
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({})
  const [isSaving, setIsSaving] = useState(false)
  const [feedback, setFeedback] = useState<FormFeedback | null>(null)
  const [showPassword, setShowPassword] = useState({
    emby_token: false,
    telegram_token: false,
    wecom_secret: false,
    tmdb_key: false
  })
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const loadNotifications = async () => {
    try {
      setLoadingState({ isLoading: true, error: null })
      const notificationsData = await api.getNotifications()
      setData(notificationsData)

      // Initialize form state from loaded data
      const config = (notificationsData as any).config || {}
      const newFormState: FormState = {
        emby: config.emby || { enabled: false },
        telegram: { ...{enabled: false, admin_users: [], regular_users: []}, ...config.telegram },
        discord: config.discord || { enabled: false },
        wecom: { ...{ enabled: false, user_list: [] }, ...config.wecom },
        tmdb: config.tmdb || { enabled: false }
      }
      setFormState(newFormState)
      setOriginalFormState(newFormState)
    } catch (error) {
      console.error('Failed to load notifications:', error)
      setLoadingState({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load notifications data'
      })
    } finally {
      setLoadingState(prev => ({ ...prev, isLoading: false }))
    }
  }

  useEffect(() => {
    loadNotifications()
  }, [])

  const handleRefresh = () => {
    loadNotifications()
  }

  const isValidUrl = (url: string): boolean => {
    if (!url) return true
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {}

    if (formState.emby.enabled) {
      if (!formState.emby.server_url?.trim()) {
        errors['emby.server_url'] = 'Server URL is required'
      } else if (!isValidUrl(formState.emby.server_url)) {
        errors['emby.server_url'] = 'Invalid URL format'
      }
      if (!formState.emby.api_token?.trim()) {
        errors['emby.api_token'] = 'API token is required'
      }
    }

    if (formState.telegram.enabled) {
      if (!formState.telegram.bot_token?.trim()) {
        errors['telegram.bot_token'] = 'Bot token is required'
      }
    }

    if (formState.discord.enabled) {
      if (!formState.discord.webhook_url?.trim()) {
        errors['discord.webhook_url'] = 'Webhook URL is required'
      } else if (!isValidUrl(formState.discord.webhook_url)) {
        errors['discord.webhook_url'] = 'Invalid URL format'
      }
    }

    if (formState.wecom.enabled) {
      if (!formState.wecom.corp_id?.trim()) {
        errors['wecom.corp_id'] = 'Corp ID is required'
      }
      if (!formState.wecom.corp_secret?.trim()) {
        errors['wecom.corp_secret'] = 'Corp secret is required'
      }
      if (!formState.wecom.agent_id?.trim()) {
        errors['wecom.agent_id'] = 'Agent ID is required'
      }
    }

    if (formState.tmdb.enabled) {
      if (!formState.tmdb.api_key?.trim()) {
        errors['tmdb.api_key'] = 'API key is required'
      }
      if (formState.tmdb.base_url && !isValidUrl(formState.tmdb.base_url)) {
        errors['tmdb.base_url'] = 'Invalid URL format'
      }
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const parseListInput = (input: string): string[] => {
    return input
      .split(/[,\n;]/)
      .map(item => item.trim())
      .filter(item => item.length > 0)
  }

  const handleInputChange = (channel: keyof FormState, field: string, value: any) => {
    setFormState(prev => ({
      ...prev,
      [channel]: {
        ...prev[channel],
        [field]: value
      }
    }))
    if (validationErrors[`${channel}.${field}`]) {
      setValidationErrors(prev => ({
        ...prev,
        [`${channel}.${field}`]: ''
      }))
    }
  }

  const handleListInputChange = (channel: keyof FormState, field: string, value: string) => {
    const arrayValue = parseListInput(value)
    handleInputChange(channel, field, arrayValue)
  }

  const handleSave = async () => {
    if (!validateForm()) {
      setFeedback({
        message: 'Please fix validation errors',
        type: 'error'
      })
      return
    }

    setIsSaving(true)
    try {
      // Process the form state to clean up empty optional fields
      const payload = {
        emby: formState.emby.enabled ? {
          enabled: true,
          server_url: formState.emby.server_url?.trim(),
          api_token: formState.emby.api_token?.trim(),
          webhook_url: formState.emby.webhook_url?.trim()
        } : { enabled: false },
        telegram: formState.telegram.enabled ? {
          enabled: true,
          bot_token: formState.telegram.bot_token?.trim(),
          admin_users: formState.telegram.admin_users || [],
          regular_users: formState.telegram.regular_users || []
        } : { enabled: false, admin_users: [], regular_users: [] },
        discord: formState.discord.enabled ? {
          enabled: true,
          webhook_url: formState.discord.webhook_url?.trim(),
          username: formState.discord.username?.trim(),
          avatar_url: formState.discord.avatar_url?.trim()
        } : { enabled: false },
        wecom: formState.wecom.enabled ? {
          enabled: true,
          corp_id: formState.wecom.corp_id?.trim(),
          corp_secret: formState.wecom.corp_secret?.trim(),
          agent_id: formState.wecom.agent_id?.trim(),
          proxy_url: formState.wecom.proxy_url?.trim(),
          user_list: formState.wecom.user_list || []
        } : { enabled: false, user_list: [] },
        tmdb: formState.tmdb.enabled ? {
          enabled: true,
          api_key: formState.tmdb.api_key?.trim(),
          base_url: formState.tmdb.base_url?.trim()
        } : { enabled: false }
      }

      await api.updateNotificationSettings([{
        id: 'notification_channels',
        name: 'Notification Channels',
        enabled: true,
        notification_types: [],
        recipients: [],
        conditions: payload
      }])

      setOriginalFormState(formState)
      setFeedback({
        message: 'Settings saved successfully',
        type: 'success'
      })

      setTimeout(() => {
        setFeedback(null)
      }, 3000)

      await loadNotifications()
    } catch (error) {
      setFeedback({
        message: error instanceof Error ? error.message : 'Failed to save settings',
        type: 'error'
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setFormState(originalFormState)
    setValidationErrors({})
    setFeedback(null)
  }

  const hasChanges = JSON.stringify(formState) !== JSON.stringify(originalFormState)

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  // 加载中状态
  if (loadingState.isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
        className="space-y-6"
      >
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 text-primary animate-spin" />
          <span className="ml-2 text-[var(--color-text-muted)]">加载通知设置...</span>
        </div>
      </motion.div>
    )
  }

  // 错误状态
  if (loadingState.error || !data) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
        className="space-y-6"
      >
        <div className="flex items-center justify-center py-12">
          <AlertCircle className="w-6 h-6 text-red-500" />
          <span className="ml-2 text-red-500">
            {loadingState.error || '加载通知数据失败'}
          </span>
        </div>
        <div className="flex justify-center">
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            重试
          </button>
        </div>
      </motion.div>
    )
  }

  const sections = [
    { id: 'settings' as const, label: '通知设置', icon: Settings },
    { id: 'templates' as const, label: '模板管理', icon: FileText },
    { id: 'preview' as const, label: '预览测试', icon: Send },
    { id: 'history' as const, label: '发送历史', icon: Clock },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
      className="space-y-6"
    >
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
            <Bell className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">通知管理</h1>
            <p className="text-sm text-[var(--color-text-muted)]">
              配置系统通知设置、模板和发送历史
            </p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-[var(--color-content2)] hover:bg-[var(--color-hover-overlay)] border border-[var(--color-border)] rounded-lg transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {/* 导航标签 */}
      <div className="flex items-center gap-1 p-1 bg-[var(--color-content2)] rounded-xl">
        {sections.map((section) => {
          const Icon = section.icon
          const isActive = activeSection === section.id
          return (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors flex-1 justify-center ${
                isActive
                  ? 'bg-[var(--color-content1)] text-primary shadow-sm'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{section.label}</span>
            </button>
          )
        })}
      </div>

      {/* 内容区域 */}
      <div className="bg-[var(--color-content1)] rounded-xl p-6 border border-[var(--color-border)]">
        {activeSection === 'settings' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4">通知渠道配置</h2>
              <p className="text-sm text-[var(--color-text-muted)] mb-6">
                配置不同的通知渠道来接收系统通知。选中启用某个渠道后，填入相应的配置信息。
              </p>
            </div>

            {/* Feedback messages */}
            {feedback && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className={`p-4 rounded-lg border flex items-start gap-3 ${
                  feedback.type === 'success'
                    ? 'bg-green-500/10 border-green-500/20'
                    : 'bg-red-500/10 border-red-500/20'
                }`}
              >
                {feedback.type === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                )}
                <span className={`text-sm ${
                  feedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {feedback.message}
                </span>
              </motion.div>
            )}

            {/* Channel Configuration Cards */}
            <div className="space-y-4">
              {/* Emby */}
              <ChannelCard
                title="Emby Server"
                description="Connect to your Emby server for media library integration"
                enabled={formState.emby.enabled}
                onEnabledChange={(value) => handleInputChange('emby', 'enabled', value)}
              >
                <div className="space-y-4">
                  <FormField
                    label="Server URL"
                    type="text"
                    value={formState.emby.server_url || ''}
                    onChange={(value) => handleInputChange('emby', 'server_url', value.trim())}
                    placeholder="https://emby.example.com"
                    error={validationErrors['emby.server_url']}
                    helperText="The base URL of your Emby server (e.g., https://emby.example.com)"
                  />

                  <FormField
                    label="API Token"
                    type="password"
                    value={formState.emby.api_token || ''}
                    onChange={(value) => handleInputChange('emby', 'api_token', value)}
                    placeholder="Your Emby API token"
                    error={validationErrors['emby.api_token']}
                    helperText="Your Emby server API token for authentication"
                    isPassword={true}
                    showPassword={showPassword.emby_token}
                    onTogglePassword={() => setShowPassword(prev => ({ ...prev, emby_token: !prev.emby_token }))}
                  />

                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-sm">
                    <p className="text-blue-700 dark:text-blue-300 font-medium mb-2">Webhook URL</p>
                    <div className="bg-[var(--color-content2)] rounded px-3 py-2 flex items-center justify-between font-mono text-xs">
                      <span className="text-[var(--color-text-muted)] truncate">
                        {formState.emby.webhook_url || `https://your-domain.com/api/notifications/emby`}
                      </span>
                      <button
                        onClick={() => copyToClipboard(
                          formState.emby.webhook_url || `https://your-domain.com/api/notifications/emby`,
                          'emby-webhook'
                        )}
                        className="ml-2 p-1 hover:bg-[var(--color-hover-overlay)] rounded transition-colors"
                      >
                        <Copy className={`w-4 h-4 ${copiedField === 'emby-webhook' ? 'text-green-500' : 'text-[var(--color-text-muted)]'}`} />
                      </button>
                    </div>
                    <p className="text-blue-600/80 dark:text-blue-400/80 mt-2">
                      Register this URL in your Emby server settings under Webhooks
                    </p>
                  </div>
                </div>
              </ChannelCard>

              {/* Telegram */}
              <ChannelCard
                title="Telegram"
                description="Send notifications to Telegram via bot"
                enabled={formState.telegram.enabled}
                onEnabledChange={(value) => handleInputChange('telegram', 'enabled', value)}
              >
                <div className="space-y-4">
                  <FormField
                    label="Bot Token"
                    type="password"
                    value={formState.telegram.bot_token || ''}
                    onChange={(value) => handleInputChange('telegram', 'bot_token', value)}
                    placeholder="Your Telegram bot token"
                    error={validationErrors['telegram.bot_token']}
                    helperText="Get this from @BotFather on Telegram"
                    isPassword={true}
                    showPassword={showPassword.telegram_token}
                    onTogglePassword={() => setShowPassword(prev => ({ ...prev, telegram_token: !prev.telegram_token }))}
                  />

                  <FormField
                    label="Admin Users"
                    type="text"
                    value={(formState.telegram.admin_users || []).join(', ')}
                    onChange={(value) => handleListInputChange('telegram', 'admin_users', value)}
                    placeholder="123456789, 987654321"
                    helperText="Comma or semicolon separated list of admin user IDs"
                  />

                  <FormField
                    label="Regular Users"
                    type="text"
                    value={(formState.telegram.regular_users || []).join(', ')}
                    onChange={(value) => handleListInputChange('telegram', 'regular_users', value)}
                    placeholder="111111111, 222222222"
                    helperText="Comma or semicolon separated list of user IDs for notifications"
                  />
                </div>
              </ChannelCard>

              {/* Discord */}
              <ChannelCard
                title="Discord"
                description="Send notifications to Discord channels via webhook"
                enabled={formState.discord.enabled}
                onEnabledChange={(value) => handleInputChange('discord', 'enabled', value)}
              >
                <div className="space-y-4">
                  <FormField
                    label="Webhook URL"
                    type="text"
                    value={formState.discord.webhook_url || ''}
                    onChange={(value) => handleInputChange('discord', 'webhook_url', value.trim())}
                    placeholder="https://discordapp.com/api/webhooks/..."
                    error={validationErrors['discord.webhook_url']}
                    helperText="Discord webhook URL from channel settings"
                  />

                  <FormField
                    label="Bot Username"
                    type="text"
                    value={formState.discord.username || ''}
                    onChange={(value) => handleInputChange('discord', 'username', value)}
                    placeholder="NotificationBot"
                    helperText="Display name for the bot in Discord"
                  />

                  <FormField
                    label="Avatar URL"
                    type="text"
                    value={formState.discord.avatar_url || ''}
                    onChange={(value) => handleInputChange('discord', 'avatar_url', value.trim())}
                    placeholder="https://example.com/avatar.png"
                    error={validationErrors['discord.avatar_url']}
                    helperText="Optional: URL to bot avatar image"
                  />
                </div>
              </ChannelCard>

              {/* WeCom */}
              <ChannelCard
                title="WeCom (Enterprise WeChat)"
                description="Send notifications via WeCom corporate messaging"
                enabled={formState.wecom.enabled}
                onEnabledChange={(value) => handleInputChange('wecom', 'enabled', value)}
              >
                <div className="space-y-4">
                  <FormField
                    label="Corp ID"
                    type="text"
                    value={formState.wecom.corp_id || ''}
                    onChange={(value) => handleInputChange('wecom', 'corp_id', value.trim())}
                    placeholder="Your WeCom Corp ID"
                    error={validationErrors['wecom.corp_id']}
                  />

                  <FormField
                    label="Corp Secret"
                    type="password"
                    value={formState.wecom.corp_secret || ''}
                    onChange={(value) => handleInputChange('wecom', 'corp_secret', value)}
                    placeholder="Your WeCom Corp Secret"
                    error={validationErrors['wecom.corp_secret']}
                    isPassword={true}
                    showPassword={showPassword.wecom_secret}
                    onTogglePassword={() => setShowPassword(prev => ({ ...prev, wecom_secret: !prev.wecom_secret }))}
                  />

                  <FormField
                    label="Agent ID"
                    type="text"
                    value={formState.wecom.agent_id || ''}
                    onChange={(value) => handleInputChange('wecom', 'agent_id', value.trim())}
                    placeholder="Your WeCom Agent ID"
                    error={validationErrors['wecom.agent_id']}
                  />

                  <FormField
                    label="Proxy URL"
                    type="text"
                    value={formState.wecom.proxy_url || ''}
                    onChange={(value) => handleInputChange('wecom', 'proxy_url', value.trim())}
                    placeholder="https://proxy.example.com"
                    helperText="Optional: Proxy URL for WeCom API calls"
                  />

                  <FormField
                    label="User List"
                    type="text"
                    value={(formState.wecom.user_list || []).join(', ')}
                    onChange={(value) => handleListInputChange('wecom', 'user_list', value)}
                    placeholder="user1, user2, user3"
                    helperText="Comma or semicolon separated list of WeCom user IDs"
                  />
                </div>
              </ChannelCard>

              {/* TMDB */}
              <ChannelCard
                title="TMDB (The Movie Database)"
                description="Integration with TMDB for enhanced media information"
                enabled={formState.tmdb.enabled}
                onEnabledChange={(value) => handleInputChange('tmdb', 'enabled', value)}
              >
                <div className="space-y-4">
                  <FormField
                    label="API Key"
                    type="password"
                    value={formState.tmdb.api_key || ''}
                    onChange={(value) => handleInputChange('tmdb', 'api_key', value)}
                    placeholder="Your TMDB API key"
                    error={validationErrors['tmdb.api_key']}
                    helperText="Get your API key from https://www.themoviedb.org/settings/api"
                    isPassword={true}
                    showPassword={showPassword.tmdb_key}
                    onTogglePassword={() => setShowPassword(prev => ({ ...prev, tmdb_key: !prev.tmdb_key }))}
                  />

                  <FormField
                    label="Base URL"
                    type="text"
                    value={formState.tmdb.base_url || ''}
                    onChange={(value) => handleInputChange('tmdb', 'base_url', value.trim())}
                    placeholder="https://api.themoviedb.org"
                    error={validationErrors['tmdb.base_url']}
                    helperText="Optional: Custom TMDB API base URL"
                  />
                </div>
              </ChannelCard>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 justify-end pt-6 border-t border-[var(--color-border)]">
              <button
                onClick={handleCancel}
                disabled={!hasChanges || isSaving}
                className="px-6 py-2 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-hover-overlay)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <X className="w-4 h-4" />
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || isSaving}
                className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    保存设置
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {activeSection === 'templates' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold mb-4">通知模板</h2>
            {data.templates.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3" />
                <p className="text-[var(--color-text-muted)]">暂无通知模板</p>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">
                  创建您的第一个通知模板
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {data.templates.map((template) => (
                  <div
                    key={template.id}
                    className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]"
                  >
                    <h3 className="font-medium mb-2">{template.name}</h3>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-[var(--color-text-muted)]">主题: </span>
                        <span>{template.subject}</span>
                      </div>
                      <div>
                        <span className="text-[var(--color-text-muted)]">类型: </span>
                        <span className="px-2 py-1 bg-[var(--color-content1)] rounded text-xs">
                          {template.template_type}
                        </span>
                      </div>
                      {template.variables.length > 0 && (
                        <div>
                          <span className="text-[var(--color-text-muted)]">变量: </span>
                          <span>{template.variables.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeSection === 'preview' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold mb-4">模板预览</h2>
            <div className="text-center py-8">
              <Send className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3" />
              <p className="text-[var(--color-text-muted)]">模板预览功能即将推出</p>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                您很快将能够预览和测试通知模板
              </p>
            </div>
          </div>
        )}

        {activeSection === 'history' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold mb-4">发送历史</h2>
            <div className="text-center py-8">
              <Clock className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3" />
              <p className="text-[var(--color-text-muted)]">暂无发送历史</p>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                发送通知后将显示历史记录
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 底部说明 */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Bell className="w-5 h-5 text-blue-500 mt-0.5" />
          <div className="text-sm">
            <p className="text-blue-600 dark:text-blue-400 font-medium mb-1">
              通知功能配置说明
            </p>
            <p className="text-blue-600/80 dark:text-blue-400/80">
              启用各个通知渠道并填入相应配置后，系统将能够通过这些渠道发送通知。所有敏感信息（如密钥和令牌）都会被加密存储。
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

interface ChannelCardProps {
  title: string
  description: string
  enabled: boolean
  onEnabledChange: (value: boolean) => void
  children: React.ReactNode
}

function ChannelCard({ title, description, enabled, onEnabledChange, children }: ChannelCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)] transition-all"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-base">{title}</h3>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">{description}</p>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onEnabledChange(e.target.checked)}
            className="w-5 h-5 rounded border-[var(--color-border)] bg-[var(--color-content1)] checked:bg-primary checked:border-primary cursor-pointer"
          />
          <span className="text-sm font-medium text-[var(--color-text-muted)]">
            {enabled ? '已启用' : '未启用'}
          </span>
        </label>
      </div>

      {enabled && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
        >
          {children}
        </motion.div>
      )}
    </motion.div>
  )
}

interface FormFieldProps {
  label: string
  type: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  error?: string
  helperText?: string
  isPassword?: boolean
  showPassword?: boolean
  onTogglePassword?: () => void
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
  error,
  helperText,
  isPassword,
  showPassword,
  onTogglePassword
}: FormFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
        {label}
      </label>
      <div className="relative">
        <input
          type={isPassword && !showPassword ? 'password' : 'text'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full px-4 py-2 rounded-lg bg-[var(--color-content1)] border transition-colors focus:outline-none ${
            error
              ? 'border-red-500 focus:border-red-500'
              : 'border-[var(--color-border)] focus:border-primary'
          }`}
        />
        {isPassword && (
          <button
            type="button"
            onClick={onTogglePassword}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
          >
            {showPassword ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>
        )}
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-red-500 text-xs mt-1"
        >
          {error}
        </motion.p>
      )}
      {helperText && !error && (
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          {helperText}
        </p>
      )}
    </div>
  )
}
