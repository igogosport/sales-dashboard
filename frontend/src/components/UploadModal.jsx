import { useState, useRef } from 'react'
import axios from 'axios'

export default function UploadModal({ onClose, onSuccess }) {
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState(null)   // null | 'uploading' | 'done' | 'error'
  const [result, setResult] = useState(null)
  const inputRef = useRef()

  const upload = async (file) => {
    if (!file) return
    setStatus('uploading')
    setResult(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await axios.post('/api/upload/sales', form)
      setResult(data)
      setStatus('done')
      onSuccess?.()
    } catch (e) {
      setResult({ error: e.response?.data?.detail || e.message })
      setStatus('error')
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    upload(e.dataTransfer.files[0])
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: '#0009', zIndex: 200,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 16, padding: 32, width: 480, boxShadow: '0 16px 48px #0006',
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>上傳銷售資料 CSV</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: 18 }}>✕</button>
        </div>

        <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 16 }}>
          從 ECOUNT 匯出銷售 CSV，上傳後自動更新儀表板。<br />
          支援 UTF-8 / Big5 編碼，重複訂單號會自動更新不重複新增。
        </div>

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          style={{
            border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
            borderRadius: 12, padding: '40px 20px', textAlign: 'center',
            cursor: 'pointer', marginBottom: 16,
            background: dragging ? '#1d4ed820' : 'transparent',
            transition: 'all 0.15s',
          }}
        >
          {status === 'uploading'
            ? <span style={{ color: 'var(--text2)' }}>上傳中…</span>
            : <>
                <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
                <div style={{ color: 'var(--text2)', fontSize: 13 }}>拖放 CSV 到這裡，或點擊選擇檔案</div>
              </>
          }
          <input ref={inputRef} type='file' accept='.csv' style={{ display: 'none' }}
            onChange={e => upload(e.target.files[0])} />
        </div>

        {/* Result */}
        {status === 'done' && result && (
          <div style={{ background: '#14532d30', border: '1px solid #22c55e40', borderRadius: 8, padding: 14, fontSize: 13 }}>
            <div style={{ color: 'var(--green)', fontWeight: 600, marginBottom: 8 }}>✅ 上傳成功</div>
            <div style={{ color: 'var(--text2)' }}>
              新增：<b style={{ color: 'var(--text)' }}>{result.inserted}</b> 筆
              更新：<b style={{ color: 'var(--text)' }}>{result.updated}</b> 筆
              跳過：<b style={{ color: 'var(--text)' }}>{result.skipped}</b> 筆
            </div>
          </div>
        )}

        {status === 'error' && result && (
          <div style={{ background: '#7f1d1d30', border: '1px solid #ef444440', borderRadius: 8, padding: 14, fontSize: 13, color: 'var(--red)' }}>
            ❌ {result.error}
          </div>
        )}
      </div>
    </div>
  )
}
