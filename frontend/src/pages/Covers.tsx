import { useState, useEffect, type ChangeEvent } from 'react'
import { Image, Download, Upload, Loader2, Play, Settings, Palette } from 'lucide-react'

interface Library {
  id: string
  name: string
  collectionType: string
}

interface CoverConfig {
  style: 'single_1' | 'single_2' | 'multi_1'
  use_title: boolean
  use_blur: boolean
  use_macaron: boolean
  use_film_grain: boolean
  poster_count: number
  blur_size: number
  color_ratio: number
  font_size_ratio: number
  date_font_size_ratio: number
  is_animated: boolean
  frame_count: number
  frame_duration: number
  output_format: 'gif' | 'webp'
}

const STYLE_INFO = {
  single_1: {
    name: '单图 1',
    description: '单张海报，模糊背景',
    preview: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImJnMSIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM2NjY2ZmY7c3RvcC1vcGFjaXR5OjEiIC8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojYWFhYWZmO3N0b3Atb3BhY2l0eToxIiAvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iNjAwIiBmaWxsPSJ1cmwoI2JnMSkiLz48ZyBvcGFjaXR5PSIwLjEiPjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iNjAwIiBmaWxsPSJ1cmwoI2JnMSkiIGZpbHRlcj0iYmx1cigzMHB4KSIvPjwvZz48cmVjdCB4PSIxMDAiIHk9IjEwMCIgd2lkdGg9IjIwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNmZmYiIHJ4PSIxMiIgZmlsdGVyPSJkcm9wLXNoYWRvdygwIDRweCA4cHggcmdiYSgwLDAsMCwwLjMpKSIvPjx0ZXh0IHg9IjIwMCIgeT0iNDUwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNmZmYiIGZvbnQtd2VpZ2h0PSJib2xkIj7ljZXlm77po47moLw8L3RleHQ+PC9zdmc+'
  },
  single_2: {
    name: '单图 2', 
    description: '单张海报，颜色混合',
    preview: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImJnMiIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNmZjY2OTk7c3RvcC1vcGFjaXR5OjEiIC8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojZmZhYWNjO3N0b3Atb3BhY2l0eToxIiAvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iNjAwIiBmaWxsPSJ1cmwoI2JnMikiLz48cmVjdCB4PSI4MCIgeT0iMTAwIiB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2ZmZiIgcng9IjEyIiBmaWx0ZXI9ImRyb3Atc2hhZG93KDAgNHB4IDhweCByZ2JhKDAsMCwwLDAuMykpIi8+PHJlY3QgeD0iMTIwIiB5PSIxMDAiIHdpZHRoPSIyMDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjNjZmZmNjIiBvcGFjaXR5PSIwLjYiIHJ4PSIxMiIvPjx0ZXh0IHg9IjIwMCIgeT0iNDUwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNmZmYiIGZvbnQtd2VpZ2h0PSJib2xkIj7popzoibLmt7flkIg8L3RleHQ+PC9zdmc+'
  },
  multi_1: {
    name: '多图 1',
    description: '3×3海报拼贴阵列',
    preview: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImJnMyIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM2NmZmY2M7c3RvcC1vcGFjaXR5OjEiIC8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojYWFmZmVlO3N0b3Atb3BhY2l0eToxIiAvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iNjAwIiBmaWxsPSJ1cmwoI2JnMykiLz48ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSg1MCw4MCkiPjxyZWN0IHg9IjAiIHk9IjAiIHdpZHRoPSI5MCIgaGVpZ2h0PSIxMzUiIGZpbGw9IiNmZjY2NjYiIHJ4PSI4IiBmaWx0ZXI9ImRyb3Atc2hhZG93KDAgMnB4IDRweCByZ2JhKDAsMCwwLDAuMikpIi8+PHJlY3QgeD0iMTA1IiB5PSIwIiB3aWR0aD0iOTAiIGhlaWdodD0iMTM1IiBmaWxsPSIjNjZmZjY2IiByeD0iOCIgZmlsdGVyPSJkcm9wLXNoYWRvdygwIDJweCA0cHggcmdiYSgwLDAsMCwwLjIpKSIvPjxyZWN0IHg9IjIxMCIgeT0iMCIgd2lkdGg9IjkwIiBoZWlnaHQ9IjEzNSIgZmlsbD0iIzY2NjZmZiIgcng9IjgiIGZpbHRlcj0iZHJvcC1zaGFkb3coMCAycHggNHB4IHJnYmEoMCwwLDAsMC4yKSkiLz48cmVjdCB4PSIwIiB5PSIxNTAiIHdpZHRoPSI5MCIgaGVpZ2h0PSIxMzUiIGZpbGw9IiNmZmNjNjYiIHJ4PSI4IiBmaWx0ZXI9ImRyb3Atc2hhZG93KDAgMnB4IDRweCByZ2JhKDAsMCwwLDAuMikpIi8+PHJlY3QgeD0iMTA1IiB5PSIxNTAiIHdpZHRoPSI5MCIgaGVpZ2h0PSIxMzUiIGZpbGw9IiNmZjY2Y2MiIHJ4PSI4IiBmaWx0ZXI9ImRyb3Atc2hhZG93KDAgMnB4IDRweCByZ2JhKDAsMCwwLDAuMikpIi8+PHJlY3QgeD0iMjEwIiB5PSIxNTAiIHdpZHRoPSI5MCIgaGVpZ2h0PSIxMzUiIGZpbGw9IiM2NmZmY2MiIHJ4PSI4IiBmaWx0ZXI9ImRyb3Atc2hhZG93KDAgMnB4IDRweCByZ2JhKDAsMCwwLDAuMikpIi8+PHJlY3QgeD0iMCIgeT0iMzAwIiB3aWR0aD0iOTAiIGhlaWdodD0iMTM1IiBmaWxsPSIjY2M2NmZmIiByeD0iOCIgZmlsdGVyPSJkcm9wLXNoYWRvdygwIDJweCA0cHggcmdiYSgwLDAsMCwwLjIpKSIvPjxyZWN0IHg9IjEwNSIgeT0iMzAwIiB3aWR0aD0iOTAiIGhlaWdodD0iMTM1IiBmaWxsPSIjZmY5OTY2IiByeD0iOCIgZmlsdGVyPSJkcm9wLXNoYWRvdygwIDJweCA0cHggcmdiYSgwLDAsMCwwLjIpKSIvPjxyZWN0IHg9IjIxMCIgeT0iMzAwIiB3aWR0aD0iOTAiIGhlaWdodD0iMTM1IiBmaWxsPSIjNjZjY2ZmIiByeD0iOCIgZmlsdGVyPSJkcm9wLXNoYWRvdygwIDJweCA0cHggcmdiYSgwLDAsMCwwLjIpKSIvPjwvZz48dGV4dCB4PSIyMDAiIHk9IjU1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjZmZmIiBmb250LXdlaWdodD0iYm9sZCI+5Yqo55S754S15b2xPC90ZXh0Pjwvc3ZnPg=='
  }
}

export default function Covers() {
  const [activeTab, setActiveTab] = useState<'style' | 'single' | 'multi' | 'animation'>('style')
  const [libraries, setLibraries] = useState<Library[]>([])
  const [selectedLibrary, setSelectedLibrary] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [generatedImage, setGeneratedImage] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState<CoverConfig>({
    style: 'multi_1',
    use_title: true,
    use_blur: true,
    use_macaron: true,
    use_film_grain: true,
    poster_count: 9,
    blur_size: 15,
    color_ratio: 0.7,
    font_size_ratio: 0.12,
    date_font_size_ratio: 0.05,
    is_animated: false,
    frame_count: 30,
    frame_duration: 50,
    output_format: 'gif'
  })

  useEffect(() => {
    fetchLibraries()
  }, [])

  const fetchLibraries = async () => {
    try {
      const response = await fetch('/api/cover/libraries')
      if (response.ok) {
        const result = await response.json()
        const librariesData = result.data || result
        setLibraries(librariesData)
        if (librariesData.length > 0) {
          setSelectedLibrary(librariesData[0].id)
        }
      }
    } catch (error) {
      console.error('获取媒体库失败:', error)
    }
  }

  const handleGenerate = async () => {
    if (!selectedLibrary) {
      setError('请选择媒体库')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/cover/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_id: selectedLibrary,
          ...config
        })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        if (generatedImage) {
          URL.revokeObjectURL(generatedImage)
        }
        setGeneratedImage(url)
      } else {
        const errorData = await response.json()
        setError(`生成失败: ${errorData.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('生成封面失败:', error)
      setError('生成封面失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!selectedLibrary) {
      setError('请选择媒体库')
      return
    }

    setUploading(true)
    setError(null)
    try {
      const uploadResponse = await fetch(`/api/cover/upload/${selectedLibrary}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_id: selectedLibrary,
          library_name: libraries.find((lib: Library) => lib.id === selectedLibrary)?.name || '',
          ...config
        })
      })

      if (uploadResponse.ok) {
        await uploadResponse.json()
        setError(null)
        alert('上传成功！封面已应用到Emby媒体库')
      } else {
        const errorData = await uploadResponse.json()
        setError(`上传失败: ${errorData.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('上传封面失败:', error)
      setError('上传封面失败，请检查网络连接')
    } finally {
      setUploading(false)
    }
  }

  const tabs = [
    { id: 'style', label: '封面风格', icon: Palette },
    { id: 'single', label: '单图设置', icon: Image },
    { id: 'multi', label: '多图设置', icon: Settings },
    { id: 'animation', label: '动画设置', icon: Play },
  ] as const

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 顶部标题栏 */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Image className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  媒体库封面生成
                </h1>
                <p className="text-gray-500 mt-1">为 Emby 媒体库自动生成精美的自定义封面</p>
              </div>
            </div>
          </div>
        </div>

        {/* 媒体库选择 */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-6">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            媒体库服务器
          </label>
          <select
            value={selectedLibrary}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedLibrary(e.target.value)}
            className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-700 font-medium"
          >
            <option value="">选择媒体库...</option>
            {libraries.map((lib: Library) => (
              <option key={lib.id} value={lib.id}>
                {lib.name} ({lib.collectionType})
              </option>
            ))}
          </select>
        </div>

        {/* 标签页导航 */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 mb-6 overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50">
            <nav className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 px-6 py-4 text-sm font-semibold transition-all flex items-center justify-center gap-2 border-b-3 ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600 bg-white'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* 标签页内容 */}
          <div className="p-8">
            {/* 封面风格选择标签页 */}
            {activeTab === 'style' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900">选择封面风格</h3>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.use_title}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_title: e.target.checked })}
                        className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm font-medium text-gray-700">显示标题</span>
                    </label>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-6">
                  {(['single_1', 'single_2', 'multi_1'] as const).map((style) => (
                    <div
                      key={style}
                      onClick={() => setConfig({ ...config, style })}
                      className={`group cursor-pointer relative rounded-2xl overflow-hidden transition-all duration-300 ${
                        config.style === style
                          ? 'ring-4 ring-blue-500 shadow-2xl scale-[1.02]'
                          : 'ring-1 ring-gray-200 hover:ring-2 hover:ring-blue-300 hover:shadow-xl'
                      }`}
                    >
                      {/* 预览图 */}
                      <div className="aspect-[2/3] bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
                        <img 
                          src={STYLE_INFO[style].preview} 
                          alt={STYLE_INFO[style].name}
                          className="w-full h-full object-cover"
                        />
                        {config.style === style && (
                          <div className="absolute inset-0 bg-blue-600 bg-opacity-10 backdrop-blur-[1px]"></div>
                        )}
                      </div>
                      
                      {/* 信息卡片 */}
                      <div className={`p-6 ${config.style === style ? 'bg-blue-50' : 'bg-white'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-lg font-bold text-gray-900">{STYLE_INFO[style].name}</h4>
                          {config.style === style && (
                            <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center">
                              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{STYLE_INFO[style].description}</p>
                      </div>

                      {/* 选中效果 */}
                      {config.style === style && (
                        <div className="absolute top-3 left-3 px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full shadow-lg">
                          已选择
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* 单图设置标签页 */}
          {activeTab === 'single' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">单图风格设置</h3>
              
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-200">
                <div className="mb-6">
                  <label className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-gray-800">模糊半径</span>
                    <span className="text-lg font-bold text-blue-600">{config.blur_size}px</span>
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="5"
                    value={config.blur_size}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, blur_size: parseInt(e.target.value) })}
                    className="w-full h-3 bg-white rounded-lg appearance-none cursor-pointer shadow-inner"
                    style={{
                      background: `linear-gradient(to right, rgb(59, 130, 246) 0%, rgb(59, 130, 246) ${((config.blur_size - 5) / 45) * 100}%, #e5e7eb ${((config.blur_size - 5) / 45) * 100}%, #e5e7eb 100%)`
                    }}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>轻度模糊 (5px)</span>
                    <span>重度模糊 (50px)</span>
                  </div>
                </div>

                <div className="mb-6">
                  <label className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-gray-800">颜色混合比例</span>
                    <span className="text-lg font-bold text-purple-600">{(config.color_ratio * 100).toFixed(0)}%</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.color_ratio}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, color_ratio: parseFloat(e.target.value) })}
                    className="w-full h-3 bg-white rounded-lg appearance-none cursor-pointer shadow-inner"
                    style={{
                      background: `linear-gradient(to right, rgb(147, 51, 234) 0%, rgb(147, 51, 234) ${config.color_ratio * 100}%, #e5e7eb ${config.color_ratio * 100}%, #e5e7eb 100%)`
                    }}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>无混合 (0%)</span>
                    <span>全混合 (100%)</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-blue-200">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={config.use_film_grain}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_film_grain: e.target.checked })}
                        className="w-6 h-6 text-blue-600 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 cursor-pointer"
                      />
                    </div>
                    <div className="flex-1">
                      <span className="text-sm font-semibold text-gray-800 block">添加胶片颗粒效果</span>
                      <span className="text-xs text-gray-600">模拟复古电影质感</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* 多图设置标签页 */}
          {activeTab === 'multi' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">多图风格设置</h3>
              
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-200">
                <div className="mb-6">
                  <label className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-gray-800">海报数量</span>
                    <span className="text-lg font-bold text-purple-600">{config.poster_count} 张</span>
                  </label>
                  <input
                    type="range"
                    min="4"
                    max="16"
                    step="1"
                    value={config.poster_count}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, poster_count: parseInt(e.target.value) })}
                    className="w-full h-3 bg-white rounded-lg appearance-none cursor-pointer shadow-inner"
                    style={{
                      background: `linear-gradient(to right, rgb(147, 51, 234) 0%, rgb(147, 51, 234) ${((config.poster_count - 4) / 12) * 100}%, #e5e7eb ${((config.poster_count - 4) / 12) * 100}%, #e5e7eb 100%)`
                    }}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-2">
                    <span>最少 (4张)</span>
                    <span>最多 (16张)</span>
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-purple-200">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={config.use_blur}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_blur: e.target.checked })}
                        className="w-6 h-6 text-purple-600 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 cursor-pointer"
                      />
                    </div>
                    <div className="flex-1">
                      <span className="text-sm font-semibold text-gray-800 block">使用模糊效果</span>
                      <span className="text-xs text-gray-600">背景图片添加柔和模糊</span>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={config.use_title}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_title: e.target.checked })}
                        className="w-6 h-6 text-purple-600 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 cursor-pointer"
                      />
                    </div>
                    <div className="flex-1">
                      <span className="text-sm font-semibold text-gray-800 block">显示标题文本</span>
                      <span className="text-xs text-gray-600">在封面上添加媒体库名称</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* 动画设置标签页 */}
          {activeTab === 'animation' && (
            <div className="space-y-6">
              <h3 className="text-xl font-bold text-gray-900 mb-6">动画封面设置</h3>
              
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-2xl p-6 mb-6 shadow-lg">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-yellow-900" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-yellow-900 mb-1">注意事项</p>
                    <p className="text-sm text-yellow-800">
                      动画封面生成时间较长，建议使用较少的帧数以提高生成速度。更多帧数会使动画更流畅，但生成时间会相应增加。
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl p-6 border border-green-200">
                <label className="flex items-center gap-3 cursor-pointer group mb-6">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={config.is_animated}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, is_animated: e.target.checked })}
                      className="w-7 h-7 text-green-600 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 cursor-pointer"
                    />
                  </div>
                  <div className="flex-1">
                    <span className="text-base font-bold text-gray-800 block">启用动画封面生成</span>
                    <span className="text-sm text-gray-600">创建动态变化的媒体库封面</span>
                  </div>
                </label>

                {config.is_animated && (
                  <div className="space-y-6 pt-6 border-t border-green-200">
                    <div>
                      <label className="flex items-center justify-between mb-3">
                        <span className="text-sm font-semibold text-gray-800">动画帧数</span>
                        <span className="text-lg font-bold text-green-600">{config.frame_count} 帧</span>
                      </label>
                      <input
                        type="range"
                        min="15"
                        max="60"
                        step="5"
                        value={config.frame_count}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, frame_count: parseInt(e.target.value) })}
                        className="w-full h-3 bg-white rounded-lg appearance-none cursor-pointer shadow-inner"
                        style={{
                          background: `linear-gradient(to right, rgb(16, 185, 129) 0%, rgb(16, 185, 129) ${((config.frame_count - 15) / 45) * 100}%, #e5e7eb ${((config.frame_count - 15) / 45) * 100}%, #e5e7eb 100%)`
                        }}
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>快速 (15帧)</span>
                        <span>流畅 (60帧)</span>
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center justify-between mb-3">
                        <span className="text-sm font-semibold text-gray-800">帧间隔时间</span>
                        <span className="text-lg font-bold text-teal-600">{config.frame_duration}ms</span>
                      </label>
                      <input
                        type="range"
                        min="30"
                        max="100"
                        step="10"
                        value={config.frame_duration}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, frame_duration: parseInt(e.target.value) })}
                        className="w-full h-3 bg-white rounded-lg appearance-none cursor-pointer shadow-inner"
                        style={{
                          background: `linear-gradient(to right, rgb(20, 184, 166) 0%, rgb(20, 184, 166) ${((config.frame_duration - 30) / 70) * 100}%, #e5e7eb ${((config.frame_duration - 30) / 70) * 100}%, #e5e7eb 100%)`
                        }}
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>快速 (30ms)</span>
                        <span>缓慢 (100ms)</span>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-green-200">
                      <label className="block text-sm font-semibold text-gray-800 mb-4">输出格式</label>
                      <div className="grid grid-cols-2 gap-4">
                        <label className={`flex items-center justify-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          config.output_format === 'gif'
                            ? 'bg-green-100 border-green-500 shadow-md'
                            : 'bg-white border-gray-300 hover:border-green-300 hover:shadow'
                        }`}>
                          <input
                            type="radio"
                            name="output_format"
                            value="gif"
                            checked={config.output_format === 'gif'}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, output_format: e.target.value as 'gif' | 'webp' })}
                            className="w-5 h-5 text-green-600"
                          />
                          <div className="flex-1">
                            <span className="text-sm font-bold text-gray-900 block">GIF 格式</span>
                            <span className="text-xs text-gray-600">广泛兼容</span>
                          </div>
                        </label>

                        <label className={`flex items-center justify-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          config.output_format === 'webp'
                            ? 'bg-green-100 border-green-500 shadow-md'
                            : 'bg-white border-gray-300 hover:border-green-300 hover:shadow'
                        }`}>
                          <input
                            type="radio"
                            name="output_format"
                            value="webp"
                            checked={config.output_format === 'webp'}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, output_format: e.target.value as 'gif' | 'webp' })}
                            className="w-5 h-5 text-green-600"
                          />
                          <div className="flex-1">
                            <span className="text-sm font-bold text-gray-900 block">WebP 格式</span>
                            <span className="text-xs text-gray-600">体积更小</span>
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 操作按钮区域 */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
        <div className="flex gap-4">
          <button
            onClick={handleGenerate}
            disabled={loading || !selectedLibrary}
            className="flex-1 px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3 font-bold text-lg group"
          >
            {loading ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                <span>生成中...</span>
              </>
            ) : (
              <>
                <Play className="w-6 h-6 group-hover:scale-110 transition-transform" />
                <span>生成封面</span>
              </>
            )}
          </button>

          <button
            onClick={handleUpload}
            disabled={loading || !generatedImage || !selectedLibrary}
            className="flex-1 px-8 py-4 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl hover:from-green-700 hover:to-green-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3 font-bold text-lg group"
          >
            {uploading ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                <span>上传中...</span>
              </>
            ) : (
              <>
                <Upload className="w-6 h-6 group-hover:scale-110 transition-transform" />
                <span>上传到 Emby</span>
              </>
            )}
          </button>
        </div>

        {(!selectedLibrary) && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
            <p className="text-sm text-yellow-800 text-center">
              <strong>提示：</strong>请先选择一个媒体库
            </p>
          </div>
        )}
      </div>

      {/* 预览区域 */}
      {generatedImage && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mt-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">封面预览</h2>
          <div className="flex justify-center">
            <div className="relative group">
              <img
                src={generatedImage}
                alt="Generated Cover"
                className="max-w-md rounded-xl shadow-2xl ring-4 ring-blue-100 transition-transform group-hover:scale-105"
              />
              <div className="absolute inset-0 rounded-xl bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-6">
                <a
                  href={generatedImage}
                  download="library_cover.jpg"
                  className="px-6 py-3 bg-white text-gray-900 rounded-lg font-semibold shadow-lg hover:bg-gray-100 transition-colors flex items-center gap-2"
                >
                  <Download className="w-5 h-5" />
                  下载封面
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {error && (
        <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-6 mt-6 shadow-lg">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-red-900 mb-1">操作失败</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
