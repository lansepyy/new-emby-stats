import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bell, Settings, FileText, Send, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { api } from '@/services/api'
import type { NotificationsData } from '@/types'

interface LoadingState {
  isLoading: boolean
  error: string | null
}

export function Notifications() {
  const [data, setData] = useState<NotificationsData | null>(null)
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    error: null
  })
  const [activeSection, setActiveSection] = useState<'settings' | 'templates' | 'preview' | 'history'>('settings')

  const loadNotifications = async () => {
    try {
      setLoadingState({ isLoading: true, error: null })
      const notificationsData = await api.getNotifications()
      setData(notificationsData)
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
          <div className="space-y-4">
            <h2 className="text-lg font-semibold mb-4">通知设置</h2>
            {data.settings.length === 0 ? (
              <div className="text-center py-8">
                <Settings className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3" />
                <p className="text-[var(--color-text-muted)]">暂无通知设置</p>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">
                  配置您的第一个通知设置以开始使用
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {data.settings.map((setting) => (
                  <div
                    key={setting.id}
                    className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{setting.name}</h3>
                      <div className="flex items-center gap-2">
                        {setting.enabled ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border-2 border-[var(--color-text-muted)]" />
                        )}
                        <span className={`text-xs px-2 py-1 rounded ${
                          setting.enabled ? 'bg-green-500/20 text-green-600' : 'bg-[var(--color-text-muted)]/20 text-[var(--color-text-muted)]'
                        }`}>
                          {setting.enabled ? '已启用' : '已禁用'}
                        </span>
                      </div>
                    </div>
                    {setting.description && (
                      <p className="text-sm text-[var(--color-text-muted)] mb-2">
                        {setting.description}
                      </p>
                    )}
                    <div className="text-xs text-[var(--color-text-muted)]">
                      通知类型: {setting.notification_types.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            )}
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
              通知功能开发中
            </p>
            <p className="text-blue-600/80 dark:text-blue-400/80">
              当前为功能预览版本。设置、模板和发送功能的后端接口已准备就绪，
              完整的管理界面和编辑器正在开发中。
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}