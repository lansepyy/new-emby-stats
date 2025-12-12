import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Folder, File, ChevronRight, Loader2 } from 'lucide-react'
import { api } from '@/services/api'

interface FilePickerModalProps {
  open: boolean
  onClose: () => void
  onSelect: (path: string) => void
  initialPath?: string
  title?: string
  description?: string
}

interface FileItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
}

export function FilePickerModal({
  open,
  onClose,
  onSelect,
  initialPath = '/',
  title = '选择文件',
  description = '浏览并选择文件',
}: FilePickerModalProps) {
  const [currentPath, setCurrentPath] = useState(initialPath)
  const [files, setFiles] = useState<FileItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      loadFiles(currentPath)
    }
  }, [open, currentPath])

  const loadFiles = async (path: string) => {
    setIsLoading(true)
    setError('')
    try {
      const data = await api.browseFiles(path)
      setFiles(data.files || [])
    } catch (err: any) {
      setError(err.message || '加载文件失败')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileClick = (file: FileItem) => {
    if (file.type === 'directory') {
      setCurrentPath(file.path)
    } else {
      onSelect(file.path)
      onClose()
    }
  }

  const handleGoUp = () => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/'
    setCurrentPath(parentPath)
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-[var(--color-content1)] rounded-2xl shadow-2xl z-50 max-h-[80vh] flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
              <div>
                <h2 className="text-lg font-semibold">{title}</h2>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">{description}</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-[var(--color-hover-overlay)] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Path */}
            <div className="px-4 py-3 bg-[var(--color-content2)] border-b border-[var(--color-border)] flex items-center gap-2">
              <span className="text-sm text-[var(--color-text-muted)]">当前路径:</span>
              <span className="text-sm font-mono">{currentPath}</span>
              {currentPath !== '/' && (
                <button
                  onClick={handleGoUp}
                  className="ml-auto text-sm text-primary hover:underline"
                >
                  返回上级
                </button>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : error ? (
                <div className="p-4 rounded-lg bg-danger/10 border border-danger/20 text-danger text-sm">
                  {error}
                </div>
              ) : files.length === 0 ? (
                <div className="text-center py-12 text-[var(--color-text-muted)]">
                  此目录为空
                </div>
              ) : (
                <div className="space-y-1">
                  {files.map((file) => (
                    <button
                      key={file.path}
                      onClick={() => handleFileClick(file)}
                      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[var(--color-hover-overlay)] transition-colors text-left"
                    >
                      {file.type === 'directory' ? (
                        <Folder className="w-5 h-5 text-primary flex-shrink-0" />
                      ) : (
                        <File className="w-5 h-5 text-[var(--color-text-muted)] flex-shrink-0" />
                      )}
                      <span className="flex-1 truncate">{file.name}</span>
                      {file.type === 'directory' && (
                        <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] flex-shrink-0" />
                      )}
                      {file.type === 'file' && file.size !== undefined && (
                        <span className="text-xs text-[var(--color-text-muted)] flex-shrink-0">
                          {formatFileSize(file.size)}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-[var(--color-border)] flex justify-end gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-hover-overlay)] transition-colors"
              >
                取消
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
