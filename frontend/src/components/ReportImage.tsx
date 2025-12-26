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
        className="font-sans"
        style={{ 
          padding: 0, 
          margin: 0,
          width: '1080px',
          backgroundColor: '#1a202c',
          color: '#ffffff'
        }}
      >
        {/* 标题区 */}
        <div style={{ padding: '50px 50px 50px 50px' }}>
          <h1 style={{ fontSize: '72px', fontWeight: 'bold', marginBottom: '20px', lineHeight: '2', paddingTop: '8px', paddingBottom: '8px' }}>{data.title}</h1>
          <p style={{ fontSize: '36px', color: '#9ca3af', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>{data.period}</p>
        </div>

        {/* 统计卡片 */}
        <div style={{ padding: '0 50px 50px 50px' }}>
          <div style={{ backgroundColor: '#2d3748', borderRadius: '20px', padding: '45px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
              {/* 观看时长 */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '52px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '15px', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>
                  {hours}小时{minutes}分
                </div>
                <div style={{ fontSize: '20px', color: '#9ca3af', lineHeight: '2', paddingTop: '4px', paddingBottom: '4px' }}>观看时长</div>
              </div>

              {/* 播放次数 */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '52px', fontWeight: 'bold', color: '#a78bfa', marginBottom: '15px', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>
                  {data.summary.total_plays}次
                </div>
                <div style={{ fontSize: '20px', color: '#9ca3af', lineHeight: '2', paddingTop: '4px', paddingBottom: '4px' }}>播放次数</div>
              </div>

              {/* 观看内容 */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '52px', fontWeight: 'bold', color: '#fbbf24', marginBottom: '15px', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>
                  {data.top_content.length}部
                </div>
                <div style={{ fontSize: '20px', color: '#9ca3af', lineHeight: '2', paddingTop: '4px', paddingBottom: '4px' }}>观看内容</div>
              </div>
            </div>

            {/* 底部详细 */}
            <div style={{ textAlign: 'center', fontSize: '22px', color: '#9ca3af', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>
              电影 {movieCount}部 · {Math.floor(movieHours)}h{Math.floor((movieHours % 1) * 60)}m
              {'    '}
              剧集 {episodeCount}集 · {Math.floor(episodeHours)}h{Math.floor((episodeHours % 1) * 60)}m
            </div>
          </div>
        </div>

        {/* 热门内容 */}
        <div style={{ padding: '0 50px 50px 50px' }}>
          <h2 style={{ fontSize: '42px', fontWeight: 'bold', marginBottom: '40px', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>热门内容</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {data.top_content.slice(0, 5).map((item, index) => {
              const itemHours = Math.floor(item.hours)
              const itemMinutes = Math.floor((item.hours % 1) * 60)
              
              return (
                <div
                  key={index}
                  style={{
                    backgroundColor: '#2d3748',
                    borderRadius: '16px',
                    padding: '25px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '25px',
                    minHeight: '140px'
                  }}
                >
                  {/* 排名 */}
                  <div style={{ 
                    fontSize: '52px', 
                    fontWeight: 'bold', 
                    color: '#fbbf24', 
                    width: '75px', 
                    textAlign: 'center',
                    flexShrink: 0,
                    lineHeight: '2',
                    paddingTop: '6px',
                    paddingBottom: '6px'
                  }}>
                    #{index + 1}
                  </div>

                  {/* 封面 */}
                  {item.item_id && coverImages[item.item_id] ? (
                    <img
                      src={coverImages[item.item_id]}
                      alt={item.name}
                      style={{ width: '90px', height: '120px', objectFit: 'cover', borderRadius: '8px', flexShrink: 0 }}
                      crossOrigin="anonymous"
                    />
                  ) : (
                    <div style={{ 
                      width: '90px', 
                      height: '120px', 
                      backgroundColor: '#374151', 
                      borderRadius: '8px', 
                      flexShrink: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <span style={{ color: '#6b7280', fontSize: '14px' }}>无封面</span>
                    </div>
                  )}

                  {/* 内容信息 */}
                  <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <h3 style={{ 
                      fontSize: '30px', 
                      fontWeight: 'bold', 
                      marginBottom: '12px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      lineHeight: '2',
                      paddingTop: '4px',
                      paddingBottom: '4px'
                    }}>
                      {item.name.length > 24 ? item.name.substring(0, 24) + '...' : item.name}
                    </h3>
                    <p style={{ fontSize: '20px', color: '#9ca3af', marginBottom: '12px', lineHeight: '2', paddingTop: '4px', paddingBottom: '4px' }}>
                      {item.type === 'Movie' ? '电影' : '剧集'}
                    </p>
                    <p style={{ fontSize: '20px', color: '#38bdf8', lineHeight: '2', paddingTop: '4px', paddingBottom: '4px' }}>
                      {item.play_count}次播放 · {itemHours}h{itemMinutes}m
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 页脚 */}
        <div style={{ textAlign: 'center', padding: '30px 0', fontSize: '22px', color: '#9ca3af', lineHeight: '2', paddingTop: '6px', paddingBottom: '6px' }}>
          New Emby Stats
        </div>
      </div>
    )
  }
)

ReportImage.displayName = 'ReportImage'
