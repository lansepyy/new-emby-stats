import { useState } from 'react'
import { Modal } from './Modal'
import { Film, Play, User, Clock, Timer } from 'lucide-react'
import { formatDateTime, formatHours } from '@/lib/utils'

export interface PosterModalData {
  title: string
  posterUrl?: string
  posterUrlHQ?: string  // 高清海报 URL
  itemName?: string
  playCount?: number
  durationHours?: number  // 播放时长（小时）
  username?: string
  time?: string
  rank?: number
  overview?: string
}

interface PosterModalProps {
  data: PosterModalData | null
  onClose: () => void
}

export function PosterModal({ data, onClose }: PosterModalProps) {
  const [imageError, setImageError] = useState(false)

  if (!data) return null

  // 优先使用高清海报，否则使用普通海报并添加高清参数
  const displayPosterUrl = data.posterUrlHQ ||
    (data.posterUrl ? `${data.posterUrl}?maxHeight=900&maxWidth=600` : undefined)

  return (
    <Modal open={!!data} onClose={onClose}>
      <div className="bg-content1 rounded-2xl overflow-hidden border border-white/10 shadow-2xl max-h-[85vh] overflow-y-auto">
        {/* Poster - 使用 2:3 比例容器 */}
        <div className="relative bg-content2">
          <div className="relative w-full" style={{ paddingBottom: '150%' }}>
            {displayPosterUrl && !imageError ? (
              <img
                src={displayPosterUrl}
                alt={data.title}
                className="absolute inset-0 w-full h-full object-contain bg-content2"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <Film className="w-16 h-16 opacity-20" />
              </div>
            )}
            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-content1 via-transparent to-transparent pointer-events-none" />

            {/* Rank badge */}
            {data.rank && (
              <div className="absolute top-4 left-4 w-10 h-10 bg-gradient-to-br from-warning to-danger rounded-xl flex items-center justify-center text-lg font-bold shadow-lg">
                {data.rank}
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="p-5 -mt-8 relative">
          <h3 className="text-xl font-bold mb-1 line-clamp-2">{data.title}</h3>
          {data.itemName && data.itemName !== data.title && (
            <p className="text-sm text-zinc-400 mb-2 line-clamp-1">{data.itemName}</p>
          )}

          {/* Overview / 剧集介绍 */}
          {data.overview && (
            <p className="text-sm text-zinc-400 leading-relaxed mt-3 mb-4 line-clamp-4">
              {data.overview}
            </p>
          )}

          <div className="space-y-3 mt-4">
            {data.playCount && (
              <div className="flex items-center gap-3 text-sm">
                <div className="w-8 h-8 rounded-lg bg-primary/20 text-primary flex items-center justify-center">
                  <Play className="w-4 h-4" />
                </div>
                <span className="text-zinc-300">播放 <span className="text-primary font-semibold">{data.playCount}</span> 次</span>
              </div>
            )}

            {data.durationHours !== undefined && data.durationHours > 0 && (
              <div className="flex items-center gap-3 text-sm">
                <div className="w-8 h-8 rounded-lg bg-secondary/20 text-secondary flex items-center justify-center">
                  <Timer className="w-4 h-4" />
                </div>
                <span className="text-zinc-300">累计 <span className="text-secondary font-semibold">{formatHours(data.durationHours)}</span></span>
              </div>
            )}

            {data.username && (
              <div className="flex items-center gap-3 text-sm">
                <div className="w-8 h-8 rounded-lg bg-success/20 text-success flex items-center justify-center">
                  <User className="w-4 h-4" />
                </div>
                <span className="text-zinc-300">{data.username}</span>
              </div>
            )}

            {data.time && (
              <div className="flex items-center gap-3 text-sm">
                <div className="w-8 h-8 rounded-lg bg-warning/20 text-warning flex items-center justify-center">
                  <Clock className="w-4 h-4" />
                </div>
                <span className="text-zinc-300">{formatDateTime(data.time)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Modal>
  )
}
