import ReactECharts from 'echarts-for-react'

interface PieChartProps {
  data: Array<{ name: string; value: number }>
  colors?: string[]
}

const DEFAULT_COLORS = ['#006FEE', '#17c964', '#f5a524', '#f31260', '#71717a']

export function PieChart({ data, colors = DEFAULT_COLORS }: PieChartProps) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#18181b',
      borderColor: '#27272a',
      textStyle: { color: '#ECEDEE', fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        label: { show: true, color: '#a1a1aa', fontSize: 11, formatter: '{b}' },
        labelLine: { lineStyle: { color: '#3f3f46' } },
        data: data.map((item, i) => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: colors[i % colors.length] },
        })),
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: '100%', minHeight: 240 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}
