import { Card, PosterCard, PosterGridSkeleton } from '@/components/ui'
import { useTopShows, useTopContent } from '@/hooks/useStats'

interface ContentProps {
  days: number
}

export function Content({ days }: ContentProps) {
  const { data: showsData, loading: showsLoading } = useTopShows(days, 16)
  const { data: contentData, loading: contentLoading } = useTopContent(days, 18)

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h3 className="font-semibold mb-4">热门剧集</h3>
        {showsLoading ? (
          <PosterGridSkeleton count={16} />
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
            {showsData?.top_shows.map((item, index) => (
              <PosterCard
                key={`${item.show_name}-${index}`}
                title={item.show_name}
                posterUrl={item.poster_url}
                rank={index + 1}
                playCount={item.play_count}
                durationHours={item.duration_hours}
                overview={item.overview}
              />
            ))}
          </div>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="font-semibold mb-4">播放排行</h3>
        {contentLoading ? (
          <PosterGridSkeleton count={18} />
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
            {contentData?.top_content.map((item, index) => (
              <PosterCard
                key={`${item.item_name}-${index}`}
                title={item.show_name || item.name || item.item_name}
                posterUrl={item.poster_url}
                itemName={item.item_name}
                rank={index + 1}
                playCount={item.play_count}
                durationHours={item.duration_hours}
                overview={item.overview}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
