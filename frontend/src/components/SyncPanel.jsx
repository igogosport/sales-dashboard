import { useState } from 'react'
import { getSyncLogs, triggerEcountSync, triggerGsheetsSync } from '../api/client'

export default function SyncPanel({ onSync }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  const loadLogs = async () => {
    const data = await getSyncLogs()
    setLogs(data)
  }

  const handleSync = async (fn, label) => {
    setLoading(true)
    try {
      await fn()
      alert(`${label} 同步已啟動，請稍待片刻後重新整理`)
      onSync?.()
    } catch (e) {
      alert('同步失敗：' + e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => { setOpen(o => !o); loadLogs() }}
        style={{
          background: 'var(--surface2)', border: '1px solid var(--border)',
          color: 'var(--text)', padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
        }}
      >
        ⚙ 資料同步
      </button>
      {open && (
        <div style={{
          position: 'absolute', right: 0, top: 38, zIndex: 100,
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 12, padding: 20, width: 320, boxShadow: '0 8px 32px #0008',
        }}>
          <div style={{ fontWeight: 600, marginBottom: 12 }}>手動同步</div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button onClick={() => handleSync(triggerEcountSync, 'ECOUNT')} disabled={loading}
              style={{ flex: 1, padding: '8px', background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12 }}>
              ECOUNT ERP
            </button>
            <button onClick={() => handleSync(triggerGsheetsSync, 'Google Sheets')} disabled={loading}
              style={{ flex: 1, padding: '8px', background: '#15803d', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12 }}>
              Google Sheets
            </button>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 8 }}>最近同步記錄</div>
          {logs.map((l, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--border)', fontSize: 11, color: 'var(--text2)' }}>
              <span style={{ color: l.source === 'ecount' ? '#3b82f6' : '#22c55e' }}>{l.source}</span>
              <span>{l.records} 筆</span>
              <span style={{ color: l.status === 'ok' ? 'var(--green)' : 'var(--red)' }}>{l.status}</span>
              <span>{new Date(l.synced_at).toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
