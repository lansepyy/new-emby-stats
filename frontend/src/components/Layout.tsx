import { useState, type ReactNode } from 'react'
import { Chip } from '@/components/ui'
import { Play, LayoutDashboard, Flame, Users, Monitor, History, LogOut } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'

interface LayoutProps {
  children: (props: { days: number; activeTab: string; refreshKey: number }) => ReactNode
}
const TABS = [
  { id: 'overview', label: '概览', icon: LayoutDashboard },
  { id: 'content', label: '热门', icon: Flame },
  { id: 'users', label: '用户', icon: Users },
  { id: 'devices', label: '设备', icon: Monitor },
  { id: 'history', label: '历史', icon: History },
]

const TIME_RANGES = [
  { days: 7, label: '7天' },
  { days: 30, label: '30天' },
  { days: 90, label: '90天' },
  { days: 365, label: '全年' },
]

export function Layout({ children }: LayoutProps) {
  const { username, logout } = useAuth()
  const [days, setDays] = useState(7)
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshKey] = useState(0)

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-black/80 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-shrink-0">
              <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center flex-shrink-0">
                <Play className="w-5 h-5" fill="currentColor" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-semibold">Emby Stats</h1>
                <p className="text-xs text-zinc-500">播放统计分析</p>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap justify-end">
              {TIME_RANGES.map((range) => (
                <Chip
                  key={range.days}
                  active={days === range.days}
                  onClick={() => setDays(range.days)}
                >
                  {range.label}
                </Chip>
              ))}
              <div className="ml-2 pl-2 border-l border-white/10 flex items-center gap-2">
                <span className="text-xs text-zinc-400 hidden sm:inline">{username}</span>
                <button
                  onClick={logout}
                  className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="登出"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {children({ days, activeTab, refreshKey })}
      </main>

      {/* Bottom Tab Navigation - Floating */}
      <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
        <div className="flex items-center gap-1 px-2 py-2 bg-content1/70 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          {TABS.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all duration-200',
                  isActive
                    ? 'bg-primary/20 text-primary'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'
                )}
              >
                <Icon className={cn('w-5 h-5 transition-transform', isActive && 'scale-110')} />
                <span className="text-[10px] font-medium">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
