import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Film } from 'lucide-react'
import { formatDateTime } from '@/lib/utils'
import { PosterModal, type PosterModalData } from './PosterModal'

interface PosterCardProps {
  title: string
  posterUrl?: string
  itemName?: string
  rank?: number
  playCount?: number
  durationHours?: number
  username?: string
  time?: string
  showEpisode?: boolean
  className?: string
  overview?: string
}

export function PosterCard({
  title,
  posterUrl,
  itemName,
  rank,
  playCount,
  durationHours,
  username,
  time,
  showEpisode,
  className,
  overview,
}: PosterCardProps) {
  const [imageError, setImageError] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)

  // Parse episode info
  let episodeInfo = ''
  if (showEpisode && itemName && itemName.includes(' - ')) {
    const parts = itemName.split(' - ')
    if (parts.length >= 2) {
      const match = parts[1].match(/s(\d+)e(\d+)/i)
      if (match) {
        episodeInfo = `S${match[1]}E${match[2]}`
      }
    }
  }

  const displayTitle = episodeInfo ? `${title} ${episodeInfo}` : title

  const modalData: PosterModalData = {
    title: displayTitle,
    posterUrl,
    itemName,
    playCount,
    durationHours,
    username,
    time,
    rank,
    overview,
  }

  return (
    <>
      <div
        className={cn(
          'relative rounded-xl overflow-hidden bg-content1 aspect-[2/3] transition-all duration-300 cursor-pointer',
          'hover:scale-[1.03] hover:shadow-[0_20px_50px_-12px_rgba(0,111,238,0.25)]',
          className
        )}
        title={itemName || title}
        onClick={() => setModalOpen(true)}
      >
        {/* Poster image or placeholder */}
        {posterUrl && !imageError ? (
          <img
            src={posterUrl}
            alt={title}
            loading="lazy"
            className={cn(
              'w-full h-full object-cover transition-opacity duration-300',
              imageLoaded ? 'opacity-100' : 'opacity-0'
            )}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
          />
        ) : null}

        {/* Placeholder */}
        {(!posterUrl || imageError || !imageLoaded) && (
          <div
            className={cn(
              'absolute inset-0 flex items-center justify-center bg-gradient-to-br from-content2 to-content1',
              posterUrl && !imageError && !imageLoaded && 'z-0'
            )}
          >
            <Film className="w-[30%] h-[30%] opacity-20" />
          </div>
        )}

        {/* Rank badge */}
        {rank && (
          <div className="absolute top-2 left-2 w-[26px] h-[26px] bg-gradient-to-br from-warning to-danger rounded-lg flex items-center justify-center text-xs font-bold">
            {rank}
          </div>
        )}

        {/* Play count badge */}
        {playCount && (
          <div className="absolute top-2 right-2 bg-primary text-white px-2 py-0.5 rounded-md text-[11px] font-semibold">
            {playCount}次
          </div>
        )}

        {/* Overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-2.5 pt-10 bg-gradient-to-t from-black/95 via-black/70 to-transparent">
          <p className="text-xs font-semibold leading-tight line-clamp-2">{displayTitle}</p>
          {username && (
            <p className="text-[10px] text-zinc-400 mt-1 truncate">{username}</p>
          )}
          {time && (
            <p className="text-[10px] text-zinc-500">{formatDateTime(time)}</p>
          )}
        </div>
      </div>

      {/* Modal */}
      <PosterModal data={modalOpen ? modalData : null} onClose={() => setModalOpen(false)} />
    </>
  )
}
