import { useState, useEffect } from 'react'
import { Info, X } from 'lucide-react'
import { Card } from '../components/ui'
import api from '../services/api'

interface VersionInfo {
  version: string
  changelog: Record<string, string[]>
  latest_changes: string[]
}

export default function VersionBadge() {
  const [showChangelog, setShowChangelog] = useState(false)
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null)

  useEffect(() => {
    fetchVersion()
  }, [])

  const fetchVersion = async () => {
    try {
      const data = await api.getVersion()
      setVersionInfo(data)
    } catch (error) {
      console.error('获取版本信息失败:', error)
    }
  }

  if (!versionInfo) return null

  return (
    <>
      {/* 版本标识 */}
      <div className="fixed bottom-4 right-4 z-40">
        <button
          onClick={() => setShowChangelog(true)}
          className="flex items-center gap-2 px-3 py-2 bg-surface hover:bg-surface-hover border border-border rounded-lg transition-colors text-sm"
        >
          <Info className="w-4 h-4" />
          <span>v{versionInfo.version}</span>
        </button>
      </div>

      {/* 更新日志弹窗 */}
      {showChangelog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="sticky top-0 bg-surface border-b border-border p-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold">更新日志</h2>
              <button
                onClick={() => setShowChangelog(false)}
                className="p-2 hover:bg-surface-hover rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {Object.entries(versionInfo.changelog)
                .sort(([a], [b]) => b.localeCompare(a))
                .map(([version, changes]) => (
                  <div key={version} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold">v{version}</h3>
                      {version === versionInfo.version && (
                        <span className="px-2 py-1 bg-primary/20 text-primary text-xs rounded">
                          当前版本
                        </span>
                      )}
                    </div>
                    <ul className="space-y-1 text-sm text-text-secondary">
                      {changes.map((change, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-primary mt-1">•</span>
                          <span>{change}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </div>
          </Card>
        </div>
      )}
    </>
  )
}
