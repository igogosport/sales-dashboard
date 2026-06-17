import ReactECharts from 'echarts-for-react'

export default function MonthlyChart({ data, compareData, title = '月度銷售趨勢' }) {
  const months = Array.from({ length: 12 }, (_, i) => `${i + 1}月`)

  const toSeries = (rows, name, color) => ({
    name,
    type: 'line',
    smooth: true,
    data: months.map((_, i) => {
      const row = (rows ?? []).find(r => r.month === i + 1)
      return row ? Math.round(row.amount) : null
    }),
    lineStyle: { color, width: 2 },
    itemStyle: { color },
    connectNulls: false,
  })

  const years = [...new Set(data?.map(r => r.year) || [])].sort((a, b) => b - a)
  const year = years[0] ?? new Date().getFullYear()
  const prevYear = year - 1
  const currData = data?.filter(r => r.year === year) ?? []
  const prevData = compareData ?? data?.filter(r => r.year === prevYear) ?? []

  const option = {
    backgroundColor: 'transparent',
    title: { text: title, textStyle: { color: '#f1f5f9', fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => params.map(p => `${p.seriesName}: NT$${(p.value || 0).toLocaleString()}`).join('<br/>'),
    },
    legend: { textStyle: { color: '#94a3b8' }, top: 0, right: 0 },
    grid: { left: 60, right: 20, bottom: 40, top: 50 },
    xAxis: { type: 'category', data: months, axisLabel: { color: '#94a3b8' }, axisLine: { lineStyle: { color: '#334155' } } },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', formatter: v => v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },
    series: [
      toSeries(currData, `${year}年`, '#3b82f6'),
      toSeries(prevData, `${prevYear}年`, '#64748b'),
    ],
  }

  return <ReactECharts option={option} style={{ height: 300 }} />
}
