import ReactECharts from 'echarts-for-react'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316']

export default function ChannelPie({ data = [], title = '通路佔比' }) {
  const pieData = data.map((r, i) => ({
    name: r.channel || '—',
    value: Math.round(r.amount),
    itemStyle: { color: COLORS[i % COLORS.length] },
  }))

  const option = {
    backgroundColor: 'transparent',
    title: { text: title, textStyle: { color: '#f1f5f9', fontSize: 14 } },
    tooltip: {
      trigger: 'item',
      formatter: p => `${p.name}<br/>NT$${p.value?.toLocaleString()} (${p.percent}%)`,
    },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#94a3b8', fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['38%', '55%'],
      data: pieData,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 12, color: '#f1f5f9' } },
    }],
  }

  return <ReactECharts option={option} style={{ height: 280 }} />
}
