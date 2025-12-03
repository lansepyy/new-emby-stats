import { Card, PosterCard, PosterGridSkeleton } from '@/components/ui'
import { useRecent } from '@/hooks/useStats'

export function History() {
  const { data: recentData, loading } = useRecent(48)

  return (
    <div>
      <Card className="p-5">
        <h3 className="font-semibold mb-4">最近播放</h3>
        {loading ? (
          <PosterGridSkeleton count={24} />
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
            {recentData?.recent.map((item, index) => (
              <PosterCard
                key={`${item.item_name}-${item.time}-${index}`}
                title={item.show_name || item.name || item.item_name}
                posterUrl={item.poster_url}
                itemName={item.item_name}
                username={item.username}
                time={item.time}
                showEpisode
                overview={item.overview}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
