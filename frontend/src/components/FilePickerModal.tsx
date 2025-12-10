import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, File, Folder, ChevronRight } from 'lucide-react'
import { Modal } from '@/components/ui'

interface FilePickerModalProps {
  open: boolean
  onClose: () => void
  onSelect: (path: string) => void
  initialPath?: string
  title?: string
  description?: string
}

export function FilePickerModal({
  open,
  onClose,
  onSelect,
  initialPath = '/data',
  title = '选择文件',
  description = '选择文件或目录',
}: FilePickerModalProps) {
  const [currentPath, setCurrentPath] = useState(initialPath)
  const [entries, setEntries] = useState<Array<{ name: string; path: string; isDir: boolean }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 加载目录内容
  useEffect(() => {
    if (!open) return

    const loadDirectory = async () => {
      setLoading(true)
      setError('')
      try {
        // 这是一个占位符实现
        // 实际应该调用后端API来获取目录内容
        setEntries([])
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载目录失败')
      } finally {
        setLoading(false)
      }
    }

    loadDirectory()
  }, [open, currentPath])

  const handleSelect = (path: string) => {
    onSelect(path)
    onClose()
  }

  const handleNavigate = (path: string) => {
    setCurrentPath(path)
  }

  return (
    <AnimatePresence>
      {open && (
        <Modal isOpen={open} onClose={onClose}>
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-[var(--color-content1)] rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
              <div>
                <h2 className="text-lg font-semibold">{title}</h2>
                {description && <p className="text-sm text-[var(--color-text-muted)] mt-1">{description}</p>}
              </div>
              <button
                onClick={onClose}
                className="p-1 hover:bg-[var(--color-hover-overlay)] rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Path Display */}
            <div className="px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-content2)]">
              <p className="text-xs text-[var(--color-text-muted)] truncate">{currentPath}</p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <p className="text-[var(--color-text-muted)]">加载中...</p>
                </div>
              ) : error ? (
                <div className="p-4 text-center text-danger">{error}</div>
              ) : entries.length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <p className="text-[var(--color-text-muted)]">目录为空</p>
                </div>
              ) : (
                <div className="divide-y divide-[var(--color-border)]">
                  {entries.map((entry) => (
                    <button
                      key={entry.path}
                      onClick={() => entry.isDir ? handleNavigate(entry.path) : handleSelect(entry.path)}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[var(--color-content2)] transition-colors text-left"
                    >
                      {entry.isDir ? (
                        <Folder className="w-5 h-5 text-primary flex-shrink-0" />
                      ) : (
                        <File className="w-5 h-5 text-[var(--color-text-muted)] flex-shrink-0" />
                      )}
                      <span className="flex-1 truncate text-sm">{entry.name}</span>
                      {entry.isDir && <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)]" />}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex gap-2 p-4 border-t border-[var(--color-border)]">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-hover-overlay)] transition-colors text-sm"
              >
                取消
              </button>
              <button
                onClick={() => handleSelect(currentPath)}
                className="flex-1 px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors text-sm"
              >
                选择此目录
              </button>
            </div>
          </motion.div>
        </Modal>
      )}
    </AnimatePresence>
  )
}
