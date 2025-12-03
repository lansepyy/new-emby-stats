import ReactECharts from 'echarts-for-react'
import type { UserItem } from '@/types'

interface UsersChartProps {
  data: UserItem[]
}

export function UsersChart({ data }: UsersChartProps) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#18181b',
      borderColor: '#27272a',
      textStyle: { color: '#ECEDEE', fontSize: 12 },
    },
    grid: { left: '3%', right: '10%', top: '3%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'value',
      name: '小时',
      nameTextStyle: { color: '#71717a' },
      axisLine: { show: false },
      axisLabel: { color: '#71717a', fontSize: 11 },
      splitLine: { lineStyle: { color: '#27272a' } },
    },
    yAxis: {
      type: 'category',
      data: data.map((d) => d.username).reverse(),
      axisLine: { show: false },
      axisLabel: { color: '#a1a1aa', fontSize: 11 },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.duration_hours).reverse(),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#006FEE' },
              { offset: 1, color: '#338ef7' },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barWidth: '60%',
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
