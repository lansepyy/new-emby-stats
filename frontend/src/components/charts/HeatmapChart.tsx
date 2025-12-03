import ReactECharts from 'echarts-for-react'
import type { HourlyItem } from '@/types'

interface HeatmapChartProps {
  data: HourlyItem[]
}

export function HeatmapChart({ data }: HeatmapChartProps) {
  const days = ['日', '一', '二', '三', '四', '五', '六']
  const hours = Array.from({ length: 24 }, (_, i) => `${i}`)
  const heatmapData = data.map((d) => [d.hour, d.day, d.count])
  const maxCount = Math.max(...data.map((d) => d.count), 1)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#18181b',
      borderColor: '#27272a',
      textStyle: { color: '#ECEDEE', fontSize: 12 },
      formatter: (p: { data: number[] }) =>
        `周${days[p.data[1]]} ${p.data[0]}:00<br/>播放 ${p.data[2]} 次`,
    },
    grid: { left: '14%', right: '6%', top: '5%', bottom: '12%' },
    xAxis: {
      type: 'category',
      data: hours,
      axisLine: { lineStyle: { color: '#27272a' } },
      axisLabel: { color: '#71717a', fontSize: 10, interval: 3 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: days,
      axisLine: { lineStyle: { color: '#27272a' } },
      axisLabel: { color: '#71717a', fontSize: 10 },
      axisTick: { show: false },
    },
    visualMap: {
      min: 0,
      max: maxCount,
      show: false,
      inRange: { color: ['#18181b', '#004493', '#006FEE', '#338ef7'] },
    },
    series: [
      {
        type: 'heatmap',
        data: heatmapData,
        label: { show: false },
        itemStyle: { borderRadius: 3, borderColor: '#000', borderWidth: 1 },
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: '100%', minHeight: 280 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}
