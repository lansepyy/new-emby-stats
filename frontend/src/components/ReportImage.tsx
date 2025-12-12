import { forwardRef } from 'react'

interface ReportData {
  title: string
  period: string
  summary: {
    total_plays: number
    total_hours: number
  }
  top_content: Array<{
    name: string
    type: string
    play_count: number
    hours: number
    item_id?: string
  }>
}

interface ReportImageProps {
  data: ReportData
  coverImages: Record<string, string>
}

export const ReportImage = forwardRef<HTMLDivElement, ReportImageProps>(
  ({ data, coverImages }, ref) => {
    const hours = Math.floor(data.summary.total_hours)
    const minutes = Math.floor((data.summary.total_hours % 1) * 60)
    
    const movieCount = data.top_content.filter(item => item.type === 'Movie').length
    const episodeCount = data.top_content.length - movieCount
    const movieHours = data.top_content
      .filter(item => item.type === 'Movie')
      .reduce((sum, item) => sum + item.hours, 0)
    const episodeHours = data.summary.total_hours - movieHours

    return (
      <div
        ref={ref}
        className="w-[1080px] bg-[#1a202c] text-white font-sans"
        style={{ padding: 0, margin: 0 }}
      >
        {/* 标题区 */}
        <div className="px-[50px] pt-[50px] pb-[50px]">
          <h1 className="text-[72px] font-bold mb-4">{data.title}</h1>
          <p className="text-[36px] text-gray-400">{data.period}</p>
        </div>

        {/* 统计卡片 */}
        <div className="px-[50px] pb-[50px]">
          <div className="bg-[#2d3748] rounded-[20px] p-[45px]">
            <div className="grid grid-cols-3 gap-4 mb-8">
              {/* 观看时长 */}
              <div className="text-center">
                <div className="text-[52px] font-bold text-[#38bdf8] mb-3">
                  {hours}小时{minutes}分
                </div>
                <div className="text-[20px] text-gray-400">观看时长</div>
              </div>

              {/* 播放次数 */}
              <div className="text-center">
                <div className="text-[52px] font-bold text-[#a78bfa] mb-3">
                  {data.summary.total_plays}次
                </div>
                <div className="text-[20px] text-gray-400">播放次数</div>
              </div>

              {/* 观看内容 */}
              <div className="text-center">
                <div className="text-[52px] font-bold text-[#fbbf24] mb-3">
                  {data.top_content.length}部
                </div>
                <div className="text-[20px] text-gray-400">观看内容</div>
              </div>
            </div>

            {/* 底部详细 */}
            <div className="text-center text-[22px] text-gray-400">
              电影 {movieCount}部 · {Math.floor(movieHours)}h{Math.floor((movieHours % 1) * 60)}m
              {'    '}
              剧集 {episodeCount}集 · {Math.floor(episodeHours)}h{Math.floor((episodeHours % 1) * 60)}m
            </div>
          </div>
        </div>

        {/* 热门内容 */}
        <div className="px-[50px] pb-[50px]">
          <h2 className="text-[42px] font-bold mb-[35px]">热门内容</h2>
          
          <div className="space-y-5">
            {data.top_content.slice(0, 5).map((item, index) => {
              const itemHours = Math.floor(item.hours)
              const itemMinutes = Math.floor((item.hours % 1) * 60)
              
              return (
                <div
                  key={index}
                  className="bg-[#2d3748] rounded-[16px] p-[25px] flex items-center gap-[25px]"
                  style={{ minHeight: '140px' }}
                >
                  {/* 排名 */}
                  <div className="text-[52px] font-bold text-[#fbbf24] w-[75px] text-center flex-shrink-0">
                    #{index + 1}
                  </div>

                  {/* 封面 */}
                  {item.item_id && coverImages[item.item_id] ? (
                    <img
                      src={coverImages[item.item_id]}
                      alt={item.name}
                      className="w-[90px] h-[120px] object-cover rounded-lg flex-shrink-0"
                      crossOrigin="anonymous"
                    />
                  ) : (
                    <div className="w-[90px] h-[120px] bg-gray-700 rounded-lg flex-shrink-0 flex items-center justify-center">
                      <span className="text-gray-500 text-sm">无封面</span>
                    </div>
                  )}

                  {/* 内容信息 */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-[30px] font-bold mb-2 truncate">
                      {item.name.length > 24 ? item.name.substring(0, 24) + '...' : item.name}
                    </h3>
                    <p className="text-[20px] text-gray-400 mb-2">
                      {item.type === 'Movie' ? '电影' : '剧集'}
                    </p>
                    <p className="text-[20px] text-[#38bdf8]">
                      {item.play_count}次播放 · {itemHours}h{itemMinutes}m
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 页脚 */}
        <div className="text-center py-[30px] text-[22px] text-gray-400">
          Emby Stats
        </div>
      </div>
    )
  }
)

ReportImage.displayName = 'ReportImage'
