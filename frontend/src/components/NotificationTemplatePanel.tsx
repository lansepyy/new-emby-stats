import { useState, useEffect } from 'react'
import { X, Plus, Trash2, Save, Bell, Loader2, AlertCircle, Check, FileText, MessageSquare, TestTube } from 'lucide-react'
import { api } from '@/services/api'
import { cn } from '@/lib/utils'

interface NotificationTemplate {
  id: string
  name: string
  channel: string
  template_content: string
  variables: string[]
  created_at: string
  updated_at: string
}

interface WeComConfig {
  id: string
  name: string
  webhook_url: string
  enabled: boolean
  created_at: string
  updated_at: string
}

interface NotificationTemplatePanelProps {
  isOpen: boolean
  onClose: () => void
}

export function NotificationTemplatePanel({ isOpen, onClose }: NotificationTemplatePanelProps) {
  const [activeTab, setActiveTab] = useState<'templates' | 'wecom' | 'send'>('templates')
  const [templates, setTemplates] = useState<NotificationTemplate[]>([])
  const [wecomConfigs, setWeComConfigs] = useState<WeComConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  
  // 模板编辑状态
  const [editingTemplate, setEditingTemplate] = useState<NotificationTemplate | null>(null)
  const [templateForm, setTemplateForm] = useState({
    name: '',
    channel: 'wecom',
    template_content: '',
    variables: [] as string[]
  })
  
  // 企业微信配置编辑状态
  const [editingConfig, setEditingConfig] = useState<WeComConfig | null>(null)
  const [configForm, setConfigForm] = useState({
    name: '',
    webhook_url: '',
    enabled: true
  })
  
  // 发送通知状态
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [selectedConfig, setSelectedConfig] = useState<string>('')
  const [contextData, setContextData] = useState<Record<string, string>>({})
  const [previewContent, setPreviewContent] = useState('')
  const [sending, setSending] = useState(false)

  // 加载数据
  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  const loadData = async () => {
    setLoading(true)
    try {
      const [templatesRes, configsRes] = await Promise.all([
        api.getNotificationTemplates(),
        api.getWeComConfigs()
      ])
      
      if (templatesRes.status === 'ok') {
        setTemplates(templatesRes.data)
      }
      
      if (configsRes.status === 'ok') {
        setWeComConfigs(configsRes.data)
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      setMessage({ type: 'error', text: '加载数据失败' })
    } finally {
      setLoading(false)
    }
  }

  // 模板操作
  const handleCreateTemplate = () => {
    setEditingTemplate(null)
    setTemplateForm({
      name: '',
      channel: 'wecom',
      template_content: '',
      variables: []
    })
  }

  const handleEditTemplate = (template: NotificationTemplate) => {
    setEditingTemplate(template)
    setTemplateForm({
      name: template.name,
      channel: template.channel,
      template_content: template.template_content,
      variables: [...template.variables]
    })
  }

  const handleSaveTemplate = async () => {
    if (!templateForm.name || !templateForm.template_content) {
      setMessage({ type: 'error', text: '请填写模板名称和内容' })
      return
    }

    setSaving(true)
    setMessage(null)
    
    try {
      // 从模板内容中提取变量
      const variables = extractVariables(templateForm.template_content)
      
      if (editingTemplate) {
        // 更新模板
        const result = await api.updateNotificationTemplate(editingTemplate.id, {
          name: templateForm.name,
          template_content: templateForm.template_content,
          variables
        })
        
        if (result.status === 'ok') {
          setMessage({ type: 'success', text: '模板更新成功' })
          await loadData()
          setEditingTemplate(null)
        } else {
          setMessage({ type: 'error', text: result.message || '更新失败' })
        }
      } else {
        // 创建新模板
        const result = await api.createNotificationTemplate({
          name: templateForm.name,
          channel: templateForm.channel,
          template_content: templateForm.template_content,
          variables
        })
        
        if (result.status === 'ok') {
          setMessage({ type: 'success', text: '模板创建成功' })
          await loadData()
          setEditingTemplate(null)
        } else {
          setMessage({ type: 'error', text: result.message || '创建失败' })
        }
      }
    } catch (error) {
      console.error('保存模板失败:', error)
      setMessage({ type: 'error', text: '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteTemplate = async (templateId: string) => {
    if (!confirm('确定要删除这个模板吗？')) {
      return
    }

    try {
      const result = await api.deleteNotificationTemplate(templateId)
      if (result.status === 'ok') {
        setMessage({ type: 'success', text: '模板删除成功' })
        await loadData()
      } else {
        setMessage({ type: 'error', text: result.message || '删除失败' })
      }
    } catch (error) {
      console.error('删除模板失败:', error)
      setMessage({ type: 'error', text: '删除失败' })
    }
  }

  const extractVariables = (content: string): string[] => {
    const matches = content.match(/\{([^}]+)\}/g) || []
    return [...new Set(matches.map(match => match.slice(1, -1)))]
  }

  // 企业微信配置操作
  const handleCreateConfig = () => {
    setEditingConfig(null)
    setConfigForm({
      name: '',
      webhook_url: '',
      enabled: true
    })
  }

  const handleEditConfig = (config: WeComConfig) => {
    setEditingConfig(config)
    setConfigForm({
      name: config.name,
      webhook_url: config.webhook_url,
      enabled: config.enabled
    })
  }

  const handleSaveConfig = async () => {
    if (!configForm.name || !configForm.webhook_url) {
      setMessage({ type: 'error', text: '请填写配置名称和WebHook URL' })
      return
    }

    setSaving(true)
    setMessage(null)
    
    try {
      if (editingConfig) {
        // 更新配置
        const result = await api.updateWeComConfig(editingConfig.id, configForm)
        
        if (result.status === 'ok') {
          setMessage({ type: 'success', text: '配置更新成功' })
          await loadData()
          setEditingConfig(null)
        } else {
          setMessage({ type: 'error', text: result.message || '更新失败' })
        }
      } else {
        // 创建新配置
        const result = await api.createWeComConfig(configForm)
        
        if (result.status === 'ok') {
          setMessage({ type: 'success', text: '配置创建成功' })
          await loadData()
          setEditingConfig(null)
        } else {
          setMessage({ type: 'error', text: result.message || '创建失败' })
        }
      }
    } catch (error) {
      console.error('保存配置失败:', error)
      setMessage({ type: 'error', text: '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteConfig = async (configId: string) => {
    if (!confirm('确定要删除这个配置吗？')) {
      return
    }

    try {
      const result = await api.deleteWeComConfig(configId)
      if (result.status === 'ok') {
        setMessage({ type: 'success', text: '配置删除成功' })
        await loadData()
      } else {
        setMessage({ type: 'error', text: result.message || '删除失败' })
      }
    } catch (error) {
      console.error('删除配置失败:', error)
      setMessage({ type: 'error', text: '删除失败' })
    }
  }

  const handleTestConnection = async (webhook_url: string) => {
    try {
      const result = await api.testWeComConnection(webhook_url)
      if (result.status === 'ok') {
        setMessage({ 
          type: result.data.success ? 'success' : 'error', 
          text: result.data.message 
        })
      } else {
        setMessage({ type: 'error', text: result.data.message })
      }
    } catch (error) {
      console.error('测试连接失败:', error)
      setMessage({ type: 'error', text: '测试连接失败' })
    }
  }

  // 发送通知
  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplate(templateId)
    const template = templates.find(t => t.id === templateId)
    if (template) {
      // 重置上下文数据
      const newContext: Record<string, string> = {}
      template.variables.forEach(variable => {
        newContext[variable] = ''
      })
      setContextData(newContext)
      updatePreview(templateId, newContext)
    }
  }

  const handleContextChange = (variable: string, value: string) => {
    const newContext = { ...contextData, [variable]: value }
    setContextData(newContext)
    if (selectedTemplate) {
      updatePreview(selectedTemplate, newContext)
    }
  }

  const updatePreview = async (templateId: string, context: Record<string, any>) => {
    try {
      const result = await api.renderNotificationTemplate(templateId, context)
      if (result.status === 'ok') {
        setPreviewContent(result.data.rendered_content)
      }
    } catch (error) {
      console.error('预览失败:', error)
    }
  }

  const handleSendNotification = async () => {
    if (!selectedConfig || (!selectedTemplate && !previewContent)) {
      setMessage({ type: 'error', text: '请选择企业微信配置和模板' })
      return
    }

    setSending(true)
    setMessage(null)
    
    try {
      const result = await api.sendWeComNotification({
        config_id: selectedConfig,
        template_id: selectedTemplate,
        context: contextData
      })
      
      if (result.status === 'ok') {
        setMessage({ type: 'success', text: '通知发送成功' })
      } else {
        setMessage({ type: 'error', text: result.message || '发送失败' })
      }
    } catch (error) {
      console.error('发送通知失败:', error)
      setMessage({ type: 'error', text: '发送失败' })
    } finally {
      setSending(false)
    }
  }

  const handleCreateDefaults = async () => {
    if (!confirm('将创建默认通知模板，确定继续吗？')) {
      return
    }

    try {
      const result = await api.createDefaultTemplates()
      if (result.status === 'ok') {
        setMessage({ type: 'success', text: '默认模板创建成功' })
        await loadData()
      } else {
        setMessage({ type: 'error', text: result.message || '创建失败' })
      }
    } catch (error) {
      console.error('创建默认模板失败:', error)
      setMessage({ type: 'error', text: '创建失败' })
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* 遮罩 */}
      <div
        className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 面板 */}
      <div className="fixed right-0 top-0 h-full w-[600px] max-w-[95vw] bg-[var(--color-content1)] border-l border-[var(--color-border)] z-50 overflow-hidden flex flex-col shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-content2)]">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary" />
            <span className="font-medium text-[var(--color-foreground)]">通知模板管理</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[var(--color-hover-overlay)] transition-colors text-[var(--color-foreground)]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab 切换 */}
        <div className="flex border-b border-[var(--color-border)]">
          <button
            onClick={() => setActiveTab('templates')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'templates'
                ? 'text-primary border-b-2 border-primary bg-primary/5'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-foreground)]'
            )}
          >
            <FileText className="w-4 h-4" />
            模板管理
          </button>
          <button
            onClick={() => setActiveTab('wecom')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'wecom'
                ? 'text-primary border-b-2 border-primary bg-primary/5'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-foreground)]'
            )}
          >
            <MessageSquare className="w-4 h-4" />
            企业微信配置
          </button>
          <button
            onClick={() => setActiveTab('send')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
              activeTab === 'send'
                ? 'text-primary border-b-2 border-primary bg-primary/5'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-foreground)]'
            )}
          >
            <TestTube className="w-4 h-4" />
            发送通知
          </button>
        </div>

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : (
            <>
              {/* 模板管理 Tab */}
              {activeTab === 'templates' && (
                <div className="space-y-4">
                  {/* 操作按钮 */}
                  <div className="flex gap-2">
                    <button
                      onClick={handleCreateTemplate}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      新建模板
                    </button>
                    <button
                      onClick={handleCreateDefaults}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-hover-overlay)] rounded-lg transition-colors"
                    >
                      <FileText className="w-4 h-4" />
                      创建默认模板
                    </button>
                  </div>

                  {/* 模板列表 */}
                  <div className="space-y-2">
                    {templates.map((template) => (
                      <div key={template.id} className="p-3 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-medium text-[var(--color-foreground)]">{template.name}</h4>
                            <p className="text-xs text-[var(--color-text-muted)] mt-1">
                              渠道: {template.channel} | 变量: {template.variables.length}个
                            </p>
                            <p className="text-xs text-[var(--color-text-secondary)] mt-1 line-clamp-2">
                              {template.template_content}
                            </p>
                          </div>
                          <div className="flex gap-1 ml-2">
                            <button
                              onClick={() => handleEditTemplate(template)}
                              className="p-1.5 text-[var(--color-text-muted)] hover:text-primary hover:bg-primary/10 rounded transition-colors"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteTemplate(template.id)}
                              className="p-1.5 text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 模板编辑表单 */}
                  {(editingTemplate !== null) && (
                    <div className="mt-6 p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
                      <h4 className="font-medium text-[var(--color-foreground)] mb-4">
                        {editingTemplate ? '编辑模板' : '新建模板'}
                      </h4>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs text-[var(--color-text-muted)] mb-1">模板名称</label>
                          <input
                            type="text"
                            value={templateForm.name}
                            onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                            placeholder="输入模板名称"
                            className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-[var(--color-text-muted)] mb-1">模板内容</label>
                          <textarea
                            value={templateForm.template_content}
                            onChange={(e) => setTemplateForm({ ...templateForm, template_content: e.target.value })}
                            placeholder="输入模板内容，使用 {变量名} 占位"
                            rows={6}
                            className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                          />
                          <p className="text-xs text-[var(--color-text-muted)] mt-1">
                            使用 {'{变量名}'} 格式定义变量，例如: {'{username}'}, {'{content_title}'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 mt-4">
                        <button
                          onClick={handleSaveTemplate}
                          disabled={saving}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                        >
                          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                          保存
                        </button>
                        <button
                          onClick={() => setEditingTemplate(null)}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-hover-overlay)] rounded-lg transition-colors"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 企业微信配置 Tab */}
              {activeTab === 'wecom' && (
                <div className="space-y-4">
                  {/* 操作按钮 */}
                  <button
                    onClick={handleCreateConfig}
                    className="flex items-center gap-2 px-3 py-2 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    新建配置
                  </button>

                  {/* 配置列表 */}
                  <div className="space-y-2">
                    {wecomConfigs.map((config) => (
                      <div key={config.id} className="p-3 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium text-[var(--color-foreground)]">{config.name}</h4>
                              <span className={cn(
                                'px-2 py-0.5 text-xs rounded-full',
                                config.enabled 
                                  ? 'bg-green-500/10 text-green-500' 
                                  : 'bg-gray-500/10 text-gray-500'
                              )}>
                                {config.enabled ? '已启用' : '已禁用'}
                              </span>
                            </div>
                            <p className="text-xs text-[var(--color-text-muted)] mt-1 break-all">
                              WebHook: {config.webhook_url}
                            </p>
                          </div>
                          <div className="flex gap-1 ml-2">
                            <button
                              onClick={() => handleTestConnection(config.webhook_url)}
                              className="p-1.5 text-[var(--color-text-muted)] hover:text-green-500 hover:bg-green-500/10 rounded transition-colors"
                              title="测试连接"
                            >
                              <TestTube className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleEditConfig(config)}
                              className="p-1.5 text-[var(--color-text-muted)] hover:text-primary hover:bg-primary/10 rounded transition-colors"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteConfig(config.id)}
                              className="p-1.5 text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 配置编辑表单 */}
                  {(editingConfig !== null) && (
                    <div className="mt-6 p-4 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
                      <h4 className="font-medium text-[var(--color-foreground)] mb-4">
                        {editingConfig ? '编辑配置' : '新建配置'}
                      </h4>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs text-[var(--color-text-muted)] mb-1">配置名称</label>
                          <input
                            type="text"
                            value={configForm.name}
                            onChange={(e) => setConfigForm({ ...configForm, name: e.target.value })}
                            placeholder="输入配置名称"
                            className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs text-[var(--color-text-muted)] mb-1">WebHook URL</label>
                          <input
                            type="url"
                            value={configForm.webhook_url}
                            onChange={(e) => setConfigForm({ ...configForm, webhook_url: e.target.value })}
                            placeholder="输入企业微信机器人WebHook URL"
                            className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            id="enabled"
                            checked={configForm.enabled}
                            onChange={(e) => setConfigForm({ ...configForm, enabled: e.target.checked })}
                            className="w-4 h-4 text-primary bg-[var(--color-content1)] border-[var(--color-border)] rounded focus:ring-primary"
                          />
                          <label htmlFor="enabled" className="text-sm text-[var(--color-foreground)]">启用此配置</label>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 mt-4">
                        <button
                          onClick={handleSaveConfig}
                          disabled={saving}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                        >
                          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                          保存
                        </button>
                        <button
                          onClick={() => setEditingConfig(null)}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-hover-overlay)] rounded-lg transition-colors"
                        >
                          取消
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 发送通知 Tab */}
              {activeTab === 'send' && (
                <div className="space-y-4">
                  {/* 选择配置和模板 */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-[var(--color-text-muted)] mb-1">企业微信配置</label>
                      <select
                        value={selectedConfig}
                        onChange={(e) => setSelectedConfig(e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="">请选择配置</option>
                        {wecomConfigs.filter(c => c.enabled).map((config) => (
                          <option key={config.id} value={config.id}>
                            {config.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-xs text-[var(--color-text-muted)] mb-1">通知模板</label>
                      <select
                        value={selectedTemplate}
                        onChange={(e) => handleTemplateChange(e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="">请选择模板</option>
                        {templates.filter(t => t.channel === 'wecom').map((template) => (
                          <option key={template.id} value={template.id}>
                            {template.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* 变量输入 */}
                  {selectedTemplate && (
                    <div className="p-3 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
                      <h4 className="text-sm font-medium text-[var(--color-foreground)] mb-3">模板变量</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {templates.find(t => t.id === selectedTemplate)?.variables.map((variable) => (
                          <div key={variable}>
                            <label className="block text-xs text-[var(--color-text-muted)] mb-1">{variable}</label>
                            <input
                              type="text"
                              value={contextData[variable] || ''}
                              onChange={(e) => handleContextChange(variable, e.target.value)}
                              placeholder={`输入 ${variable}`}
                              className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-content1)] text-[var(--color-foreground)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-primary"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 预览 */}
                  {previewContent && (
                    <div className="p-3 bg-[var(--color-content2)] rounded-lg border border-[var(--color-border)]">
                      <h4 className="text-sm font-medium text-[var(--color-foreground)] mb-2">预览</h4>
                      <div className="p-3 bg-[var(--color-content1)] rounded border border-[var(--color-border)] text-sm text-[var(--color-foreground)] whitespace-pre-wrap">
                        {previewContent}
                      </div>
                    </div>
                  )}

                  {/* 发送按钮 */}
                  <button
                    onClick={handleSendNotification}
                    disabled={sending || !selectedConfig || !selectedTemplate}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                  >
                    {sending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Bell className="w-4 h-4" />
                    )}
                    发送通知
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* 底部消息栏 */}
        {message && (
          <div className="border-t border-[var(--color-border)] p-4 bg-[var(--color-content2)]">
            <div
              className={cn(
                'flex items-center gap-2 px-3 py-2 text-sm rounded-lg',
                message.type === 'success'
                  ? 'bg-green-500/10 text-green-500'
                  : 'bg-red-500/10 text-red-500'
              )}
            >
              {message.type === 'success' ? (
                <Check className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              {message.text}
            </div>
          </div>
        )}
      </div>
    </>
  )
}