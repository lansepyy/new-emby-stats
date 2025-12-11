import { useState, type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chip } from '@/components/ui'
import { Play, LayoutDashboard, Flame, Users, Monitor, History, FileText, LogOut, Sun, Moon, Filter, Settings, Bell } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { useFilter } from '@/contexts/FilterContext'
import { FilterPanel } from '@/components/FilterPanel'
import { NameMappingPanel } from '@/components/NameMappingPanel'

interface LayoutProps {
  children: (props: { activeTab: string; refreshKey: number }) => ReactNode
  hideChrome?: boolean
}
const TABS = [
  { id: 'overview', label: '概览', icon: LayoutDashboard },
  { id: 'content', label: '热门', icon: Flame },
  { id: 'users', label: '用户', icon: Users },
  { id: 'devices', label: '设备', icon: Monitor },
  { id: 'history', label: '历史', icon: History },
  { id: 'notifications', label: '通知', icon: Bell },
  { id: 'report', label: '报告', icon: FileText },
]

const TIME_RANGES = [
  { days: 7, label: '7天' },
  { days: 30, label: '30天' },
  { days: 90, label: '90天' },
  { days: 365, label: '全年' },
]

export function Layout({ children, hideChrome = false }: LayoutProps) {
  const { username, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const { filters, options, setDays, hasActiveFilters, activeFilterCount } = useFilter()
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshKey] = useState(0)
  const [filterPanelOpen, setFilterPanelOpen] = useState(false)
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false)

  return (
    <div className={cn('min-h-screen', hideChrome ? 'pb-6' : 'pb-24')}>
      {/* Header */}
      {!hideChrome && (
        <header className="sticky top-0 z-50 glass-subtle safe-area-top">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-2 sm:gap-4">
            <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-primary flex items-center justify-center flex-shrink-0">
                <Play className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-semibold">Emby Stats</h1>
                <p className="text-xs text-zinc-500">播放统计分析 v1.85</p>
              </div>
            </div>
            <div className="flex items-center gap-1 sm:gap-2 flex-wrap justify-end">
              {/* 移动端隐藏时间范围选择器，改为在筛选面板中显示 */}
              <div className="hidden sm:flex items-center gap-2">
                {TIME_RANGES.map((range) => (
                  <Chip
                    key={range.days}
                    active={!filters.useDateRange && filters.days === range.days}
                    onClick={() => setDays(range.days)}
                  >
                    {range.label}
                  </Chip>
                ))}
              </div>
              {/* 筛选按钮 */}
              <button
                onClick={() => setFilterPanelOpen(true)}
                className={cn(
                  'relative p-2 sm:p-2 rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center',
                  hasActiveFilters
                    ? 'text-primary bg-primary/10 hover:bg-primary/20'
                    : 'text-[var(--color-text-muted)] hover:text-foreground hover:bg-[var(--color-hover-overlay)]'
                )}
                title="筛选"
              >
                <Filter className="w-4 h-4 sm:w-4 sm:h-4" />
                {activeFilterCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 text-[10px] bg-primary text-white rounded-full flex items-center justify-center">
                    {activeFilterCount}
                  </span>
                )}
              </button>
              <div className="ml-1 sm:ml-2 pl-1 sm:pl-2 border-l border-[var(--color-border)] flex items-center gap-1 sm:gap-2">
                <span className="text-xs text-[var(--color-text-muted)] hidden sm:inline">{username}</span>
                <button
                  onClick={() => setSettingsPanelOpen(true)}
                  className="p-2 rounded-lg text-[var(--color-text-muted)] hover:text-foreground hover:bg-[var(--color-hover-overlay)] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                  title="设置"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-lg text-[var(--color-text-muted)] hover:text-foreground hover:bg-[var(--color-hover-overlay)] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                  title={theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
                >
                  {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>
                <button
                  onClick={logout}
                  className="p-2 rounded-lg text-[var(--color-text-muted)] hover:text-foreground hover:bg-[var(--color-hover-overlay)] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                  title="登出"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
        </header>
      )}

      {/* Main Content */}
      <main
        className={cn(
          'max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6',
          hideChrome && 'px-0 sm:px-0 py-0'
        )}
      >
        {children({ activeTab, refreshKey })}
      </main>

      {!hideChrome && (
        <>
          {/* Filter Panel */}
          <FilterPanel isOpen={filterPanelOpen} onClose={() => setFilterPanelOpen(false)} />

          {/* Name Mapping Settings Panel */}
          <NameMappingPanel
            isOpen={settingsPanelOpen}
            onClose={() => setSettingsPanelOpen(false)}
            availableClients={options?.clients || []}
            availableDevices={options?.devices || []}
          />

          {/* 底部 Tab 导航 - 面板打开时隐藏，避免遮挡 */}
          <AnimatePresence>
            {!filterPanelOpen && !settingsPanelOpen && (
              <motion.nav
                initial={{ y: 16, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 16, opacity: 0 }}
                transition={{
                  type: 'spring',
                  stiffness: 400,
                  damping: 30,
                  mass: 0.8
                }}
                className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
              >
                <div className="flex items-center gap-1 px-2 py-2 glass rounded-2xl">
                  {TABS.map((tab) => {
                    const Icon = tab.icon
                    const isActive = activeTab === tab.id
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                          'relative flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-colors duration-200',
                          isActive
                            ? 'text-primary'
                            : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-muted)]'
                        )}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="activeTabBg"
                            className="absolute inset-0 bg-primary/20 rounded-xl"
                            transition={{
                              type: 'spring',
                              stiffness: 500,
                              damping: 35,
                              mass: 0.5
                            }}
                          />
                        )}
                        <motion.div
                          animate={{ scale: isActive ? 1.08 : 1 }}
                          transition={{
                            type: 'spring',
                            stiffness: 400,
                            damping: 20
                          }}
                        >
                          <Icon className="w-5 h-5 relative z-10" />
                        </motion.div>
                        <span className="text-[10px] font-medium relative z-10">{tab.label}</span>
                      </button>
                    )
                  })}
                </div>
              </motion.nav>
            )}
          </AnimatePresence>
        </>
      )}

    </div>
  )
}
