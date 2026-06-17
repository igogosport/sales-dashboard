import ReactECharts from 'echarts-for-react'

export default function BrandChart({ data = [], title = '品牌銷售排行', valueKey = 'amount', unit = 'NT$' }) {
  const sorted = [...data].sort((a, b) => b[valueKey] - a[valueKey]).slice(0, 15)

  const option = {
    backgroundColor: 'transparent',
    title: { text: title, textStyle: { color: '#f1f5f9', fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        const val = valueKey === 'amount' ? `NT$${p.value?.toLocaleString()}` : `${p.value?.toLocaleString()} 件`
        return `${p.name}: ${val}`
      },
    },
    grid: { left: 130, right: 20, bottom: 40, top: 50 },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#94a3b8',
        formatter: v => v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v,
      },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map(r => r.brand || r.channel || '—').reverse(),
      axisLabel: { color: '#94a3b8', width: 120, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: sorted.map(r => r[valueKey]).reverse(),
      itemStyle: { color: '#3b82f6', borderRadius: [0, 4, 4, 0] },
      label: {
        show: true,
        position: 'right',
        color: '#94a3b8',
        formatter: p => valueKey === 'amount' ? `$${Math.round(p.value / 1000)}K` : p.value,
      },
    }],
  }

  return <ReactECharts option={option} style={{ height: Math.max(250, sorted.length * 30 + 80) }} />
}
