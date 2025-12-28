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
  title_text: string
  use_blur: boolean
  use_macaron: boolean
  use_film_grain: boolean
  poster_count: number
  blur_size: number
  color_ratio: number
  font_size_ratio: number
  date_font_size_ratio: number
  font_family: string
  zh_font_path: string
  en_font_path: string
  zh_font_size: number
  en_font_size: number
  is_animated: boolean
  frame_count: number
  frame_duration: number
  output_format: 'gif' | 'webp'
}

const STYLE_INFO = {
  single_1: {
    name: '单图 1',
    description: '单张海报，模糊背景',
    preview: '/single_1.jpg'
  },
  single_2: {
    name: '单图 2', 
    description: '单张海报，颜色混合',
    preview: '/single_2.jpg'
  },
  multi_1: {
    name: '多图 1',
    description: '3×3海报拼贴阵列',
    preview: '/multi_1.jpg'
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
  
  // 默认配置
  const getDefaultConfig = (): CoverConfig => {
    return {
      style: 'multi_1',
      use_title: true,
      title_text: `# 序号格式说明：
# 1. 媒体库名称:
# 2.   - 中文标题
# 3.   - 英文标题
#
# 配置示例（可复制修改）：
# 1. 华语电影:
# 2.   - 华语电影
#3.   - Chinese Movies
#
# 4. 欧美电影:
# 5.   - 欧美电影
# 6.   - Western Movies
#
# 7. 电视剧:
# 8.   - 电视剧
# 9.   - TV Series
#
# 10. 动漫:
# 11.   - 动漫
# 12.   - Anime
#
# 13. 纪录片:
# 14.   - 纪录片
# 15.   - Documentary
#
# 16. 综艺:
# 17.   - 综艺
# 18.   - Variety Shows
#
# 19. 儿童:
# 20.   - 儿童
# 21.   - Kids
#
# 22. 音乐:
# 23.   - 音乐
# 24.   - Music
#
# 25. 体育:
# 26.   - 体育
# 27.   - Sports
#
# 28. 短剧:
# 29.   - 短剧
# 30.   - Short Drama
`,
      use_blur: true,
      use_macaron: true,
      use_film_grain: true,
      poster_count: 9,
      blur_size: 15,
      color_ratio: 0.7,
      font_size_ratio: 0.12,
      date_font_size_ratio: 0.05,
      font_family: 'SourceHanSansCN-Bold.otf',
      zh_font_path: '',
      en_font_path: '',
      zh_font_size: 163,
      en_font_size: 50,
      is_animated: false,
      frame_count: 60,
      frame_duration: 50,
      output_format: 'webp'
    }
  }
  
  const [config, setConfig] = useState<CoverConfig>(getDefaultConfig())
  
  // 从后端加载配置
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch('/api/config/cover')
        if (response.ok) {
          const savedConfig = await response.json()
          setConfig(savedConfig)
        }
      } catch (e) {
        console.error('加载配置失败', e)
      }
    }
    loadConfig()
  }, [])
  
  // 自动保存配置到后端
  useEffect(() => {
    const saveConfig = async () => {
      try {
        await fetch('/api/config/cover', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(config),
        })
      } catch (e) {
        console.error('保存配置失败', e)
      }
    }
    
    // 延迟保存，避免频繁请求
    const timer = setTimeout(() => {
      saveConfig()
    }, 1000)
    
    return () => clearTimeout(timer)
  }, [config])

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
      const selectedLib = libraries.find((lib: Library) => lib.id === selectedLibrary)
      
      // 解析YAML配置获取中英文标题
      let title = selectedLib?.name || ''
      let subtitle = ''
      
      if (config.title_text && selectedLib?.name) {
        try {
          const lines = config.title_text.split('\n')
          let currentLibrary = ''
          let foundLibrary = false
          let titleCount = 0  // 记录已找到的标题数量
          
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim()
            
            // 跳过注释和空行
            if (line.startsWith('#') || !line) continue
            
            // 检查是否是媒体库名称行（以:结尾）
            if (line.endsWith(':')) {
              currentLibrary = line.slice(0, -1).trim()
              foundLibrary = currentLibrary === selectedLib.name
              titleCount = 0  // 重置计数器
            }
            // 如果找到了对应的媒体库，读取其标题
            else if (foundLibrary && line.startsWith('-')) {
              const value = line.slice(1).trim()
              if (titleCount === 0) {
                title = value  // 第一个 - 是中文标题
                titleCount++
              } else if (titleCount === 1) {
                subtitle = value  // 第二个 - 是英文标题
                break  // 找到两个标题后退出
              }
            }
          }
        } catch (e) {
          console.warn('YAML配置解析失败，使用默认标题:', e)
        }
      }
      
      const requestData = {
        library_id: selectedLibrary,
        library_name: selectedLib?.name || '',
        title: title,
        subtitle: subtitle,
        ...config
      }
      
      console.log('🎬 发送封面生成请求:', requestData)
      console.log('📊 配置详情:', {
        style: config.style,
        is_animated: config.is_animated,
        frame_count: config.frame_count,
        output_format: config.output_format
      })
      
      const response = await fetch('/api/cover/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      })

      console.log('📡 响应状态:', response.status, response.statusText)

      if (response.ok) {
        const blob = await response.blob()
        console.log('✅ 封面生成成功，大小:', blob.size, 'bytes, 类型:', blob.type)
        const url = URL.createObjectURL(blob)
        if (generatedImage) {
          URL.revokeObjectURL(generatedImage)
        }
        setGeneratedImage(url)
      } else {
        const errorText = await response.text()
        console.error('❌ 服务器返回错误:', errorText)
        let errorMsg = '生成失败'
        try {
          const errorData = JSON.parse(errorText)
          errorMsg = `生成失败: ${errorData.detail || errorText}`
        } catch {
          errorMsg = `生成失败 (${response.status}): ${errorText.substring(0, 200)}`
        }
        setError(errorMsg)
      }
    } catch (error) {
      console.error('❌ 封面生成异常:', error)
      const errorMsg = error instanceof Error ? error.message : String(error)
      setError(`生成封面失败: ${errorMsg}`)
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
                </div>

                {/* 封面标题设置 */}
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-200 mb-6">
                  <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                    </svg>
                    中英标题配置
                  </h4>
                  
                  <div className="space-y-4">
                    <div className="bg-blue-100 border-l-4 border-blue-500 p-4 rounded">
                      <p className="text-sm text-blue-900">
                        <strong>ℹ️ 提示：</strong>未配置的媒体库将默认使用媒体库名称作为封面中文标题，无副标题
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        标题配置 (YAML 格式)
                      </label>
                      <textarea
                        value={config.title_text}
                        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setConfig({ ...config, title_text: e.target.value })}
                        className="w-full px-4 py-3 bg-gray-900 text-green-400 font-mono text-sm border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        rows={15}
                        placeholder={`# 配置封面标题（按媒体库名称对应）\n# 格式如下：\n#\n# 媒体库名称:\n#   - 中文标题\n#   - 英文标题\n#\n# 示例：\n恐师片:\n  - 恐师片\n  - Horror\n\n天堂电影:\n  - 天堂电影\n  - TV`}
                        spellCheck={false}
                      />
                    </div>
                    
                    <div>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={config.use_title}
                          onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, use_title: e.target.checked })}
                          className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm font-semibold text-gray-800">显示封面标题</span>
                      </label>
                    </div>
                    
                    {config.use_title && (
                      <div className="space-y-4 pl-8">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* 中文字体配置 */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">中文字体路径</label>
                            <input
                              type="text"
                              value={config.zh_font_path}
                              onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, zh_font_path: e.target.value })}
                              placeholder="/config/fonts/你的中文字体.ttf"
                              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            />
                            <p className="text-xs text-gray-500 mt-1">留空使用默认字体</p>
                          </div>
                          
                          {/* 英文字体配置 */}
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">英文字体路径</label>
                            <input
                              type="text"
                              value={config.en_font_path}
                              onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, en_font_path: e.target.value })}
                              placeholder="/config/fonts/你的英文字体.otf"
                              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            />
                            <p className="text-xs text-gray-500 mt-1">留空使用默认字体</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* 中文字体大小 */}
                          <div>
                            <label className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-gray-700">中文字体大小</span>
                              <span className="text-sm font-bold text-blue-600">{config.zh_font_size}px</span>
                            </label>
                            <input
                              type="range"
                              min="100"
                              max="300"
                              step="1"
                              value={config.zh_font_size}
                              onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, zh_font_size: parseInt(e.target.value) })}
                              className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                              style={{
                                background: `linear-gradient(to right, rgb(59, 130, 246) 0%, rgb(59, 130, 246) ${((config.zh_font_size - 100) / 200) * 100}%, #e5e7eb ${((config.zh_font_size - 100) / 200) * 100}%, #e5e7eb 100%)`
                              }}
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                              <span>100px</span>
                              <span>300px</span>
                            </div>
                          </div>
                          
                          {/* 英文字体大小 */}
                          <div>
                            <label className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-gray-700">英文字体大小</span>
                              <span className="text-sm font-bold text-blue-600">{config.en_font_size}px</span>
                            </label>
                            <input
                              type="range"
                              min="30"
                              max="100"
                              step="1"
                              value={config.en_font_size}
                              onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, en_font_size: parseInt(e.target.value) })}
                              className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                              style={{
                                background: `linear-gradient(to right, rgb(59, 130, 246) 0%, rgb(59, 130, 246) ${((config.en_font_size - 30) / 70) * 100}%, #e5e7eb ${((config.en_font_size - 30) / 70) * 100}%, #e5e7eb 100%)`
                              }}
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                              <span>30px</span>
                              <span>100px</span>
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">字体选择（旧版，建议使用上面的字体路径）</label>
                          <select
                            value={config.font_family}
                            onChange={(e: ChangeEvent<HTMLSelectElement>) => setConfig({ ...config, font_family: e.target.value })}
                            className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          >
                            <option value="SourceHanSansCN-Bold.otf">思源黑体 Bold</option>
                            <option value="SourceHanSansCN-Regular.otf">思源黑体 Regular</option>
                            <option value="SourceHanSerifCN-Bold.otf">思源宋体 Bold</option>
                            <option value="NotoSansSC-Bold.otf">Noto Sans SC Bold</option>
                          </select>
                        </div>
                        
                        <div>
                          <label className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">字体大小</span>
                            <span className="text-sm font-bold text-blue-600">{(config.font_size_ratio * 100).toFixed(0)}%</span>
                          </label>
                          <input
                            type="range"
                            min="0.05"
                            max="0.25"
                            step="0.01"
                            value={config.font_size_ratio}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, font_size_ratio: parseFloat(e.target.value) })}
                            className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                            style={{
                              background: `linear-gradient(to right, rgb(59, 130, 246) 0%, rgb(59, 130, 246) ${((config.font_size_ratio - 0.05) / 0.2) * 100}%, #e5e7eb ${((config.font_size_ratio - 0.05) / 0.2) * 100}%, #e5e7eb 100%)`
                            }}
                          />
                          <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>较小 (5%)</span>
                            <span>较大 (25%)</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-6">
                  {(['single_1', 'single_2', 'multi_1'] as const).map((style) => (
                    <div
                      key={style}
                      onClick={() => setConfig({ ...config, style })}
                      className={`group cursor-pointer relative rounded-2xl overflow-hidden transition-all duration-300 ${
                        config.style === style
                          ? 'ring-4 ring-blue-500 shadow-2xl'
                          : 'ring-2 ring-gray-300 hover:ring-blue-400 hover:shadow-xl'
                      }`}
                    >
                      {/* 预览图 */}
                      <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden flex items-center justify-center">
                        <img 
                          src={STYLE_INFO[style].preview} 
                          alt={STYLE_INFO[style].name}
                          className="w-full h-full object-contain"
                        />
                      </div>
                      
                      {/* 信息卡片 */}
                      <div className={`p-4 ${config.style === style ? 'bg-blue-50' : 'bg-white'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-base font-bold text-gray-900">{STYLE_INFO[style].name}</h4>
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

                      {/* 选中标记 */}
                      {config.style === style && (
                        <div className="absolute top-3 right-3 px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full shadow-lg">
                          ✓ 已选择
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
              
              {/* 动画预览卡片 */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div className="bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 rounded-2xl p-4 relative overflow-hidden group" style={{ aspectRatio: '16/9' }}>
                  <div className="absolute top-3 left-3 text-white z-10">
                    <div className="text-sm font-bold">动画封面</div>
                    <div className="text-xs opacity-80">GIF 格式</div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center p-6">
                    <img 
                      src="/multi_1_animated.gif" 
                      alt="GIF动画预览"
                      className="w-full h-full object-contain rounded-lg shadow-2xl"
                    />
                  </div>
                  <div className="absolute bottom-3 right-3 text-white text-xs bg-black/30 px-2 py-1 rounded-full">
                    ▶️ 动态播放
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 rounded-2xl p-4 relative overflow-hidden" style={{ aspectRatio: '16/9' }}>
                  <div className="absolute top-3 left-3 text-white z-10">
                    <div className="text-sm font-bold">动画封面</div>
                    <div className="text-xs opacity-80">WebP 格式</div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center p-6">
                    <img 
                      src="/multi_1_animated.webp" 
                      alt="WebP动画预览"
                      className="w-full h-full object-contain rounded-lg shadow-2xl"
                    />
                  </div>
                  <div className="absolute bottom-3 right-3 text-white text-xs bg-black/30 px-2 py-1 rounded-full">
                    ⚡ 体积更小
                  </div>
                </div>
              </div>
              
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
                        min="30"
                        max="90"
                        step="5"
                        value={config.frame_count}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => setConfig({ ...config, frame_count: parseInt(e.target.value) })}
                        className="w-full h-3 bg-white rounded-lg appearance-none cursor-pointer shadow-inner"
                        style={{
                          background: `linear-gradient(to right, rgb(16, 185, 129) 0%, rgb(16, 185, 129) ${((config.frame_count - 30) / 60) * 100}%, #e5e7eb ${((config.frame_count - 30) / 60) * 100}%, #e5e7eb 100%)`
                        }}
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>快速 (30帧)</span>
                        <span>极致流畅 (90帧)</span>
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
                <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                </svg>
                <span>生成预览</span>
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
                <span>应用到 Emby</span>
              </>
            )}
          </button>
        </div>

        {(!selectedLibrary) && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
            <p className="text-sm text-yellow-800 text-center">
              <strong>💡 提示：</strong>请先选择媒体库，点击"生成预览"查看效果，确认无误后再"应用到 Emby"
            </p>
          </div>
        )}
        
        {generatedImage && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl">
            <p className="text-sm text-green-800 text-center flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
              <strong>预览已生成！</strong>请检查下方预览效果，确认无误后点击"应用到 Emby"
            </p>
          </div>
        )}
      </div>

      {/* 预览区域 */}
      {generatedImage && (
        <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-2xl border-2 border-blue-200 p-8 mt-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl"></div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                    <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">封面预览效果</h2>
                  <p className="text-sm text-gray-500">请仔细检查封面效果，确认无误后应用到 Emby</p>
                </div>
              </div>
            </div>
            
            <div className="flex flex-col items-center gap-6">
              <div className="relative group">
                <div className="absolute -inset-4 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl opacity-20 blur-xl group-hover:opacity-30 transition-opacity"></div>
                <img
                  src={generatedImage}
                  alt="Generated Cover"
                  className="relative max-w-md rounded-xl shadow-2xl ring-4 ring-white transition-all duration-300 group-hover:scale-[1.02] group-hover:shadow-3xl"
                />
                <div className="absolute inset-0 rounded-xl bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-6">
                  <a
                    href={generatedImage}
                    download="library_cover.jpg"
                    className="px-6 py-3 bg-white text-gray-900 rounded-lg font-semibold shadow-lg hover:bg-gray-100 transition-colors flex items-center gap-2"
                  >
                    <Download className="w-5 h-5" />
                    下载预览图
                  </a>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 w-full max-w-2xl">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 text-center border border-blue-200">
                  <div className="text-2xl font-bold text-blue-600 mb-1">{STYLE_INFO[config.style].name}</div>
                  <div className="text-xs text-gray-600">当前风格</div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center border border-purple-200">
                  <div className="text-2xl font-bold text-purple-600 mb-1">{config.is_animated ? config.output_format.toUpperCase() : 'JPG'}</div>
                  <div className="text-xs text-gray-600">输出格式</div>
                </div>
                <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-lg p-4 text-center border border-pink-200">
                  <div className="text-2xl font-bold text-pink-600 mb-1">{config.use_title ? '✓' : '✗'}</div>
                  <div className="text-xs text-gray-600">显示标题</div>
                </div>
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
    </div>
  )
}
