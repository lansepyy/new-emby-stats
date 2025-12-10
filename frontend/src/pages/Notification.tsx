import { useState, useEffect } from 'react'
import { Bell, Plus, TestTube, Send, FileText, MessageSquare, Clock, CheckCircle, XCircle, BarChart3 } from 'lucide-react'
import { api } from '@/services/api'
import { cn } from '@/lib/utils'

interface NotificationStats {
  total_configs: number
  enabled_configs: number
  total_sent: number
  success_sent: number
  failed_sent: number
  success_rate: number
}

interface WeComLog {
  id: number
  config_id: string
  template_id?: string
  message_content: string
  status: string
  error_message?: string
  sent_at: string
  config_name?: string
  template_name?: string
}

export function Notification() {
  const [stats, setStats] = useState<NotificationStats | null>(null)
  const [logs, setLogs] = useState<WeComLog[]>([])
  const [loading, setLoading] = useState(true)
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'logs'>('overview')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [statsRes, logsRes] = await Promise.all([
        api.getWeComStatistics(),
        api.getWeComLogs(20)
      ])
      
      if (statsRes.status === 'ok') {
        setStats(statsRes.data)
      }
      
      if (logsRes.status === 'ok') {
        setLogs(logsRes.data)
      }
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timeString: string) => {
    const date = new Date(timeString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const truncateText = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
            <Bell className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-foreground)]">通知模板管理</h1>
            <p className="text-sm text-[var(--color-text-muted)]">管理和发送企业微信通知消息</p>
          </div>
        </div>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('openNotificationPanel'))}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          管理通知模板
        </button>
      </div>

      {/* 子Tab导航 */}
      <div className="flex border-b border-[var(--color-border)]">
        <button
          onClick={() => setActiveSubTab('overview')}
          className={cn(
            'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2',
            activeSubTab === 'overview'
              ? 'text-primary border-primary bg-primary/5'
              : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-foreground)]'
          )}
        >
          <BarChart3 className="w-4 h-4" />
          统计概览
        </button>
        <button
          onClick={() => setActiveSubTab('logs')}
          className={cn(
            'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2',
            activeSubTab === 'logs'
              ? 'text-primary border-primary bg-primary/5'
              : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-foreground)]'
          )}
        >
          <Clock className="w-4 h-4" />
          发送日志
        </button>
      </div>

      {/* 统计概览 Tab */}
      {activeSubTab === 'overview' && stats && (
        <div className="space-y-6">
          {/* 统计卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">总配置数</p>
                  <p className="text-2xl font-semibold text-[var(--color-foreground)]">{stats.total_configs}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">{stats.enabled_configs} 个已启用</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                  <Send className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">总发送次数</p>
                  <p className="text-2xl font-semibold text-[var(--color-foreground)]">{stats.total_sent}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">累计发送消息</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">成功发送</p>
                  <p className="text-2xl font-semibold text-[var(--color-foreground)]">{stats.success_sent}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">次成功</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                  <XCircle className="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">失败发送</p>
                  <p className="text-2xl font-semibold text-[var(--color-foreground)]">{stats.failed_sent}</p>
                  <p className="text-xs text-[var(--color-text-muted)]">次失败</p>
                </div>
              </div>
            </div>
          </div>

          {/* 成功率 */}
          <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-[var(--color-foreground)]">通知成功率</h3>
              <span className="text-lg font-semibold text-primary">{stats.success_rate}%</span>
            </div>
            <div className="w-full bg-[var(--color-content3)] rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${stats.success_rate}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-[var(--color-text-muted)] mt-2">
              <span>失败 {stats.failed_sent} 次</span>
              <span>成功 {stats.success_sent} 次</span>
            </div>
          </div>

          {/* 快速操作 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-3 mb-3">
                <FileText className="w-5 h-5 text-primary" />
                <h3 className="text-sm font-medium text-[var(--color-foreground)]">模板管理</h3>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mb-3">
                创建和管理通知模板，定义变量和内容格式
              </p>
              <button
                onClick={() => window.dispatchEvent(new CustomEvent('openNotificationPanel'))}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-4 h-4" />
                管理模板
              </button>
            </div>

            <div className="p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-3 mb-3">
                <TestTube className="w-5 h-5 text-primary" />
                <h3 className="text-sm font-medium text-[var(--color-foreground)]">测试通知</h3>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mb-3">
                发送测试消息验证企业微信配置是否正常
              </p>
              <button
                onClick={() => window.dispatchEvent(new CustomEvent('openNotificationPanel', { detail: { tab: 'send' } }))}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm border border-primary text-primary rounded-lg hover:bg-primary/10 transition-colors"
              >
                <Send className="w-4 h-4" />
                发送测试
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 发送日志 Tab */}
      {activeSubTab === 'logs' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-[var(--color-foreground)]">最近发送日志</h3>
            <button
              onClick={loadData}
              className="text-xs text-primary hover:text-primary/80 transition-colors"
            >
              刷新
            </button>
          </div>

          {logs.length === 0 ? (
            <div className="p-8 text-center">
              <Bell className="w-8 h-8 text-[var(--color-text-muted)] mx-auto mb-2" />
              <p className="text-[var(--color-text-muted)]">暂无发送日志</p>
            </div>
          ) : (
            <div className="space-y-2">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="p-3 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn(
                          'px-2 py-0.5 text-xs rounded-full',
                          log.status === 'success'
                            ? 'bg-green-500/10 text-green-500'
                            : 'bg-red-500/10 text-red-500'
                        )}>
                          {log.status === 'success' ? '成功' : '失败'}
                        </span>
                        <span className="text-xs text-[var(--color-text-muted)]">
                          {log.config_name || '未知配置'}
                        </span>
                        {log.template_name && (
                          <span className="text-xs text-[var(--color-text-muted)]">
                            • {log.template_name}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[var(--color-foreground)] mb-1">
                        {truncateText(log.message_content)}
                      </p>
                      {log.error_message && (
                        <p className="text-xs text-red-500 mb-1">
                          错误: {truncateText(log.error_message, 50)}
                        </p>
                      )}
                      <p className="text-xs text-[var(--color-text-muted)]">
                        {formatTime(log.sent_at)}
                      </p>
                    </div>
                    <div className="flex items-center">
                      {log.status === 'success' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}