export default function KpiCard({ label, value, unit = '', change }) {
  const positive = change >= 0
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding: '20px 24px',
    }}>
      <div style={{ color: 'var(--text2)', fontSize: 12, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700 }}>
        {value?.toLocaleString()}<span style={{ fontSize: 14, marginLeft: 4, color: 'var(--text2)' }}>{unit}</span>
      </div>
      {change !== undefined && (
        <div style={{ marginTop: 6, fontSize: 12, color: positive ? 'var(--green)' : 'var(--red)' }}>
          {positive ? '▲' : '▼'} {Math.abs(change).toFixed(1)}% 較上月
        </div>
      )}
    </div>
  )
}
