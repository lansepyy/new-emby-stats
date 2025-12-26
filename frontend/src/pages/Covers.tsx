import { useState, useEffect, type ChangeEvent } from 'react'
import { Image, Download, Upload, Loader2 } from 'lucide-react'

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

const STYLE_PREVIEWS = {
  single_1: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y4ZjlmYSIvPjxyZWN0IHg9IjQwIiB5PSI0MCIgd2lkdGg9IjEyMCIgaGVpZ2h0PSIxODAiIGZpbGw9IiM2NjY2ZmYiIHJ4PSI4Ii8+PHRleHQgeD0iMTAwIiB5PSIyNTAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzMzMyI+U3R5bGUgMTwvdGV4dD48L3N2Zz4=',
  single_2: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y4ZjlmYSIvPjxyZWN0IHg9IjIwIiB5PSI0MCIgd2lkdGg9IjEyMCIgaGVpZ2h0PSIxODAiIGZpbGw9IiNmZjY2OTkiIHJ4PSI4Ii8+PHJlY3QgeD0iNjAiIHk9IjQwIiB3aWR0aD0iMTIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzY2ZmZjYyIgcng9IjgiIG9wYWNpdHk9IjAuNiIvPjx0ZXh0IHg9IjEwMCIgeT0iMjUwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiMzMzMiPlN0eWxlIDI8L3RleHQ+PC9zdmc+',
  multi_1: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y4ZjlmYSIvPjxyZWN0IHg9IjEwIiB5PSIxMCIgd2lkdGg9IjU1IiBoZWlnaHQ9Ijg1IiBmaWxsPSIjZmY2NjY2IiByeD0iNCIvPjxyZWN0IHg9IjcyIiB5PSIxMCIgd2lkdGg9IjU1IiBoZWlnaHQ9Ijg1IiBmaWxsPSIjNjZmZjY2IiByeD0iNCIvPjxyZWN0IHg9IjEzNSIgeT0iMTAiIHdpZHRoPSI1NSIgaGVpZ2h0PSI4NSIgZmlsbD0iIzY2NjZmZiIgcng9IjQiLz48cmVjdCB4PSIxMCIgeT0iMTA1IiB3aWR0aD0iNTUiIGhlaWdodD0iODUiIGZpbGw9IiNmZmNjNjYiIHJ4PSI0Ii8+PHJlY3QgeD0iNzIiIHk9IjEwNSIgd2lkdGg9IjU1IiBoZWlnaHQ9Ijg1IiBmaWxsPSIjZmY2NmNjIiByeD0iNCIvPjxyZWN0IHg9IjEzNSIgeT0iMTA1IiB3aWR0aD0iNTUiIGhlaWdodD0iODUiIGZpbGw9IiM2NmZmY2MiIHJ4PSI0Ii8+PHJlY3QgeD0iMTAiIHk9IjIwMCIgd2lkdGg9IjU1IiBoZWlnaHQ9Ijg1IiBmaWxsPSIjY2M2NmZmIiByeD0iNCIvPjxyZWN0IHg9IjcyIiB5PSIyMDAiIHdpZHRoPSI1NSIgaGVpZ2h0PSI4NSIgZmlsbD0iI2ZmOTk2NiIgcng9IjQiLz48cmVjdCB4PSIxMzUiIHk9IjIwMCIgd2lkdGg9IjU1IiBoZWlnaHQ9Ijg1IiBmaWxsPSIjNjZjY2ZmIiByeD0iNCIvPjwvc3ZnPg=='
}

const STYLE_NAMES = {
  single_1: '单图风格1',
  single_2: '单图风格2',
  multi_1: '多图风格1'
}

const STYLE_DESCRIPTIONS = {
  single_1: '单张海报，模糊背景',
  single_2: '单张海报，颜色混合',
  multi_1: '3x3海报阵列'
}

export default function Covers() {
  const [activeTab, setActiveTab] = useState<'style' | 'single' | 'multi' | 'animation' | 'advanced'>('style')
  const [libraries, setLibraries] = useState<Library[]>([])
  const [selectedLibrary, setSelectedLibrary] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string>('')
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
      alert('请选择媒体库')
      return
    }

    setLoading(true)
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
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl)
        }
        setPreviewUrl(url)
      } else {
        const error = await response.json()
        alert(`生成失败: ${error.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('生成封面失败:', error)
      alert('生成封面失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!previewUrl) return
    const a = document.createElement('a')
    a.href = previewUrl
    const ext = config.is_animated ? config.output_format : 'png'
    a.download = `cover_${selectedLibrary}_${config.style}.${ext}`
    a.click()
  }

  const handleUpload = async () => {
    if (!selectedLibrary) {
      alert('请选择媒体库')
      return
    }

    setLoading(true)
    try {
      // 使用相同的配置直接让后端生成并上传
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
        alert('上传成功！封面已应用到Emby媒体库')
      } else {
        const error = await uploadResponse.json()
        alert(`上传失败: ${error.detail || '未知错误'}`)
      }
    } catch (error) {
      console.error('上传封面失败:', error)
      alert('上传封面失败')
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'style', label: '风格选择' },
    { id: 'single', label: '单图设置' },
    { id: 'multi', label: '多图设置' },
    { id: 'animation', label: '动画设置' },
    { id: 'advanced', label: '高级选项' }
  ] as const

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Image className="w-8 h-8 text-blue-600" />
        <h1 className="text-3xl font-bold">媒体库封面生成</h1>
      </div>

      {/* 媒体库选择 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          选择媒体库
        </label>
        <select
          value={selectedLibrary}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedLibrary(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {libraries.map((lib: Library) => (
            <option key={lib.id} value={lib.id}>
              {lib.name} ({lib.collectionType})
            </option>
          ))}
        </select>
      </div>

      {/* 标签页导航 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* 标签页内容 */}
        <div className="p-6">
          {/* 风格选择标签页 */}
          {activeTab === 'style' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">选择封面风格</h3>
              <div className="grid grid-cols-3 gap-6">
                {(['single_1', 'single_2', 'multi_1'] as const).map((style) => (
                  <div
                    key={style}
                    onClick={() => setConfig({ ...config, style })}
                    className={`cursor-pointer border-2 rounded-lg p-4 transition-all hover:shadow-lg ${
                      config.style === style
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="aspect-[2/3] mb-3 bg-gray-100 rounded flex items-center justify-center overflow-hidden">
                      <img 
                        src={STYLE_PREVIEWS[style]} 
                        alt={STYLE_NAMES[style]}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-1">{STYLE_NAMES[style]}</h4>
                    <p className="text-sm text-gray-600">{STYLE_DESCRIPTIONS[style]}</p>
                    {config.style === style && (
                      <div className="mt-2 flex items-center gap-2 text-blue-600 text-sm">
                        <div className="w-4 h-4 rounded-full bg-blue-600 flex items-center justify-center">
                          <div className="w-2 h-2 bg-white rounded-full"></div>
                        </div>
                        已选择
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-200">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.use_title}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_title: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">显示标题</span>
                </label>
              </div>
            </div>
          )}

          {/* 单图设置标签页 */}
          {activeTab === 'single' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">单图风格参数</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  模糊半径: {config.blur_size}
                </label>
                <input
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={config.blur_size}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, blur_size: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>5</span>
                  <span>50</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  颜色混合比例: {(config.color_ratio * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.color_ratio}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, color_ratio: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0%</span>
                  <span>100%</span>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.use_film_grain}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_film_grain: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">添加胶片颗粒效果</span>
                </label>
              </div>
            </div>
          )}

          {/* 多图设置标签页 */}
          {activeTab === 'multi' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">多图风格参数</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  海报数量: {config.poster_count}
                </label>
                <input
                  type="range"
                  min="4"
                  max="16"
                  step="1"
                  value={config.poster_count}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, poster_count: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>4</span>
                  <span>16</span>
                </div>
              </div>

              <div className="space-y-3 pt-4 border-t border-gray-200">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.use_blur}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_blur: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">使用模糊效果</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.use_macaron}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_macaron: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">使用马卡龙配色</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.use_film_grain}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_film_grain: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">添加胶片颗粒效果</span>
                </label>
              </div>
            </div>
          )}

          {/* 动画设置标签页 */}
          {activeTab === 'animation' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">动画封面设置</h3>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-yellow-800">
                  <strong>提示:</strong> 动画封面生成时间较长，建议使用较少的帧数以提高生成速度。
                </p>
              </div>

              <div className="pt-4">
                <label className="flex items-center gap-3 mb-6">
                  <input
                    type="checkbox"
                    checked={config.is_animated}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, is_animated: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">生成动画封面</span>
                </label>
              </div>

              {config.is_animated && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      帧数: {config.frame_count}
                    </label>
                    <input
                      type="range"
                      min="15"
                      max="60"
                      step="5"
                      value={config.frame_count}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, frame_count: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>15帧</span>
                      <span>60帧</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      帧间隔: {config.frame_duration}ms
                    </label>
                    <input
                      type="range"
                      min="30"
                      max="100"
                      step="10"
                      value={config.frame_duration}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, frame_duration: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>30ms</span>
                      <span>100ms</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      输出格式
                    </label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="output_format"
                          value="gif"
                          checked={config.output_format === 'gif'}
                          onChange={(e) => setConfig({ ...config, output_format: e.target.value as 'gif' | 'webp' })}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm text-gray-700">GIF</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="output_format"
                          value="webp"
                          checked={config.output_format === 'webp'}
                          onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, output_format: e.target.value as 'gif' | 'webp' })}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm text-gray-700">WebP</span>
                      </label>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* 高级选项标签页 */}
          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">高级选项</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  标题字体大小比例: {(config.font_size_ratio * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.08"
                  max="0.20"
                  step="0.01"
                  value={config.font_size_ratio}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, font_size_ratio: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>8%</span>
                  <span>20%</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  日期字体大小比例: {(config.date_font_size_ratio * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.03"
                  max="0.10"
                  step="0.01"
                  value={config.date_font_size_ratio}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, date_font_size_ratio: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>3%</span>
                  <span>10%</span>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
                <p className="text-sm text-blue-800">
                  <strong>说明:</strong> 字体大小比例相对于图片高度计算。建议使用默认值以获得最佳视觉效果。
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex gap-4">
          <button
            onClick={handleGenerate}
            disabled={loading || !selectedLibrary}
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 font-medium"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Image className="w-5 h-5" />
                生成封面
              </>
            )}
          </button>

          <button
            onClick={handleDownload}
            disabled={!previewUrl}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium"
          >
            <Download className="w-5 h-5" />
            下载
          </button>

          <button
            onClick={handleUpload}
            disabled={!previewUrl || loading}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium"
          >
            <Upload className="w-5 h-5" />
            上传到Emby
          </button>
        </div>
      </div>

      {/* 预览区域 */}
      {previewUrl && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">封面预览</h3>
          <div className="flex justify-center">
            <img
              src={previewUrl}
              alt="封面预览"
              className="max-w-full h-auto rounded-lg shadow-lg"
              style={{ maxHeight: '600px' }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
