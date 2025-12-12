import { useState, useEffect } from 'react'
import { Card, PosterCard, PosterGridSkeleton, Avatar } from '@/components/ui'
import { Heart, Users, TrendingUp, Search, ChevronDown, ChevronUp, Film } from 'lucide-react'
import type { FilterParams } from '@/services/api'

interface FavoriteItem {
  item_id: string
  item_name: string
  item_type: string
  poster_url?: string
  backdrop_url?: string
  overview?: string
  last_favorited?: string
}

interface UserFavorites {
  user_id: string
  username: string
  favorites: FavoriteItem[]
  favorite_count: number
  movie_count?: number
  episode_count?: number
}

interface RankingItem extends FavoriteItem {
  favorite_count: number
}

interface FavoritesData {
  by_user: UserFavorites[]
  ranking: RankingItem[]
  stats: {
    total_favorites: number
    total_users: number
    active_users: number
    movie_count: number
    episode_count: number
  }
}

interface FavoritesProps {
  filterParams: FilterParams
}

type ViewMode = 'by-user' | 'ranking'
type ItemTypeFilter = 'all' | 'Movie' | 'Episode'

export function Favorites({ filterParams }: FavoritesProps) {
  const [data, setData] = useState<FavoritesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<ViewMode>('by-user')
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<ItemTypeFilter>('all')
  const [expandedUsers, setExpandedUsers] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchFavorites()
  }, [filterParams])

  const fetchFavorites = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      
      if (filterParams.startDate && filterParams.endDate) {
        params.append('start_date', filterParams.startDate)
        params.append('end_date', filterParams.endDate)
      } else if (filterParams.days) {
        params.append('days', filterParams.days.toString())
      }
      
      if (typeFilter !== 'all') {
        params.append('item_type', typeFilter)
      }

      const response = await fetch(`/api/favorites?${params}`)
      const result = await response.json()
      setData(result)
    } catch (error) {
      console.error('Failed to fetch favorites:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleUserExpand = (userId: string) => {
    const newExpanded = new Set(expandedUsers)
    if (newExpanded.has(userId)) {
      newExpanded.delete(userId)
    } else {
      newExpanded.add(userId)
    }
    setExpandedUsers(newExpanded)
  }

  const filteredUsers = data?.by_user.filter(user =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const filteredRanking = data?.ranking || []

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      {data?.stats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-pink-500/10 flex items-center justify-center">
                <Heart className="w-6 h-6 text-pink-500" />
              </div>
              <div>
                <p className="text-sm text-default-400">收藏内容</p>
                <p className="text-2xl font-semibold">{data.stats.total_favorites}</p>
              </div>
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-default-400">有收藏的用户</p>
                <p className="text-2xl font-semibold">{data.stats.active_users} / {data.stats.total_users}</p>
              </div>
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <Film className="w-6 h-6 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-default-400">电影 / 剧集</p>
                <p className="text-2xl font-semibold">{data.stats.movie_count} / {data.stats.episode_count}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* 工具栏 */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          {/* 视图切换 */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('by-user')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'by-user'
                  ? 'bg-primary text-white'
                  : 'bg-content1 hover:bg-content2'
              }`}
            >
              <Users className="w-4 h-4" />
              按用户视图
            </button>
            <button
              onClick={() => setViewMode('ranking')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'ranking'
                  ? 'bg-primary text-white'
                  : 'bg-content1 hover:bg-content2'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              热门榜单
            </button>
          </div>

          {/* 类型筛选 */}
          <div className="flex gap-2">
            {(['all', 'Movie', 'Episode'] as const).map((type) => (
              <button
                key={type}
                onClick={() => {
                  setTypeFilter(type)
                  // 类型变化后重新获取数据
                  setTimeout(() => fetchFavorites(), 0)
                }}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  typeFilter === type
                    ? 'bg-primary text-white'
                    : 'bg-content1 hover:bg-content2'
                }`}
              >
                {type === 'all' ? '全部' : type === 'Movie' ? '电影' : '剧集'}
              </button>
            ))}
          </div>

          {/* 用户搜索 (仅在按用户视图时显示) */}
          {viewMode === 'by-user' && (
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-default-400" />
              <input
                type="text"
                placeholder="搜索用户..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-content1 border border-divider focus:outline-none focus:border-primary"
              />
            </div>
          )}
        </div>
      </Card>

      {/* 内容区域 */}
      {loading ? (
        <Card className="p-5">
          <PosterGridSkeleton count={12} />
        </Card>
      ) : viewMode === 'by-user' ? (
        // 按用户视图
        <div className="space-y-3">
          {filteredUsers.length === 0 ? (
            <Card className="p-8">
              <p className="text-center text-default-400">暂无收藏数据</p>
            </Card>
          ) : (
            filteredUsers.map((user, index) => {
              const isExpanded = expandedUsers.has(user.user_id)
              
              return (
                <div key={user.user_id}>
                  <Card className="p-4">
                    {/* 用户信息行 */}
                    <div 
                      className="flex items-center justify-between cursor-pointer hover:bg-content2/50 rounded-lg -m-4 p-4 transition-colors" 
                      onClick={() => toggleUserExpand(user.user_id)}
                    >
                      <div className="flex items-center gap-3">
                        <Avatar name={user.username} index={index} />
                        <div>
                          <h3 className="font-semibold">{user.username}</h3>
                          <p className="text-xs text-default-400">
                            {user.movie_count ? `📽️ ${user.movie_count}部电影` : ''}{user.movie_count && user.episode_count ? ' ' : ''}{user.episode_count ? `📺 ${user.episode_count}部剧集` : ''}
                          </p>
                        </div>
                      </div>
                      
                      {/* 右侧：小海报预览 + 收藏数 + 展开按钮 */}
                      <div className="flex items-center gap-3">
                        {/* 小海报缩略图预览（只显示5个） */}
                        {user.favorites.length > 0 && (
                          <div className="flex gap-1">
                            {user.favorites.slice(0, Math.min(5, user.favorites.length)).map((item, idx) => (
                              <div 
                                key={item.item_id} 
                                className="w-12 h-16 rounded overflow-hidden flex-shrink-0"
                                style={{ 
                                  marginLeft: idx > 0 ? '-8px' : '0',
                                  zIndex: 5 - idx
                                }}
                              >
                                {item.poster_url ? (
                                  <img 
                                    src={item.poster_url} 
                                    alt={item.item_name}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full bg-content2 flex items-center justify-center">
                                    <Film className="w-6 h-6 text-default-300" />
                                  </div>
                                )}
                              </div>
                            ))}
                            {user.favorites.length > 5 && (
                              <div className="w-12 h-16 rounded bg-content2 flex items-center justify-center text-xs text-default-400" style={{ marginLeft: '-8px' }}>
                                +{user.favorites.length - 5}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {/* 收藏数量 */}
                        <div className="flex items-center gap-1 text-pink-500">
                          <Heart className="w-4 h-4 fill-pink-500" />
                          <span className="font-semibold">{user.favorite_count}</span>
                        </div>
                        
                        {/* 展开/收起图标 */}
                        <div className="p-1">
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                  
                  {/* 展开后的完整海报网格 */}
                  {isExpanded && user.favorites.length > 0 && (
                    <Card className="p-5 mt-2">
                      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
                        {user.favorites.map((item) => (
                          <PosterCard
                            key={item.item_id}
                            title={item.item_name}
                            posterUrl={item.poster_url}
                            backdropUrl={item.backdrop_url}
                            overview={item.overview}
                          />
                        ))}
                      </div>
                    </Card>
                  )}
                </div>
              )
            })
          )}
        </div>
      ) : (
        // 热门榜单视图
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Heart className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">收藏排行榜</h3>
          </div>
          {filteredRanking.length === 0 ? (
            <p className="text-center text-default-400 py-8">暂无数据</p>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
              {filteredRanking.map((item, index) => (
                <PosterCard
                  key={item.item_id}
                  title={item.item_name}
                  posterUrl={item.poster_url}
                  backdropUrl={item.backdrop_url}
                  rank={index + 1}
                  playCount={item.favorite_count}
                  overview={item.overview}
                />
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
