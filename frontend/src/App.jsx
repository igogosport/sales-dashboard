import { useState, useEffect, useCallback } from 'react'
import KpiCard from './components/KpiCard'
import MonthlyChart from './components/MonthlyChart'
import BrandChart from './components/BrandChart'
import ChannelPie from './components/ChannelPie'
import SyncPanel from './components/SyncPanel'
import UploadModal from './components/UploadModal'
import {
  getFilters, getSummary, getMonthlyTrend,
  getByBrand, getByChannel,
} from './api/client'

const TAB = { SALES: 'sales', PURCHASE: 'purchase' }

export default function App() {
  const [filters, setFilters] = useState({ years: [], brands: [], channels: [] })
  const [year, setYear] = useState(null)
  const [brand, setBrand] = useState('')
  const [channel, setChannel] = useState('')
  const [tab, setTab] = useState(TAB.SALES)
  const [showUpload, setShowUpload] = useState(false)

  const [summary, setSummary] = useState(null)
  const [monthly, setMonthly] = useState([])
  const [prevMonthly, setPrevMonthly] = useState([])
  const [byBrand, setByBrand] = useState([])
  const [byChannel, setByChannel] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getFilters().then(f => {
      setFilters(f)
      setYear(f.years.length ? f.years[0] : new Date().getFullYear())
    }).catch(() => {
      setFilters({ years: [2026, 2025, 2024], brands: [], channels: [] })
      setYear(new Date().getFullYear())
    })
  }, [])

  const loadData = useCallback(async () => {
    if (!year) return
    setLoading(true)
    try {
      const params = { year, brand: brand || undefined, channel: channel || undefined }
      const [s, m, pm, bb, bc] = await Promise.all([
        getSummary(params),
        getMonthlyTrend(params),
        getMonthlyTrend({ ...params, year: year - 1 }),
        getByBrand(params),
        getByChannel(params),
      ])
      setSummary(s)
      setMonthly(m)
      setPrevMonthly(pm)
      setByBrand(bb)
      setByChannel(bc)
    } catch {
      // show demo placeholder
    }
    setLoading(false)
  }, [year, brand, channel])

  useEffect(() => { loadData() }, [loadData])

  const select = (setter) => (e) => setter(e.target.value)

  const selectStyle = {
    background: 'var(--surface2)', border: '1px solid var(--border)',
    color: 'var(--text)', padding: '6px 10px', borderRadius: 8, fontSize: 13, cursor: 'pointer',
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 24px', borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 20, fontWeight: 700 }}>📊 銷售儀表板</span>
          <span style={{ color: 'var(--text2)', fontSize: 12 }}>平台 + 通路 銷售分析</span>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select style={selectStyle} value={year || ''} onChange={select(v => setYear(Number(v.target?.value || v)))}>
            {filters.years.map(y => <option key={y} value={y}>{y}年</option>)}
          </select>
          <select style={selectStyle} value={brand} onChange={select(setBrand)}>
            <option value=''>全部品牌</option>
            {filters.brands.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
          <select style={selectStyle} value={channel} onChange={select(setChannel)}>
            <option value=''>全部通路</option>
            {filters.channels.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button
            onClick={() => setShowUpload(true)}
            style={{
              background: '#1d4ed8', border: 'none',
              color: '#fff', padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
            }}
          >
            ↑ 上傳銷售 CSV
          </button>
          <SyncPanel onSync={loadData} />
        </div>
      </header>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 2, padding: '0 24px', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>
        {[{ key: TAB.SALES, label: '銷售分析' }, { key: TAB.PURCHASE, label: '採購分析' }].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: '10px 18px', border: 'none', cursor: 'pointer', fontSize: 13,
            background: 'transparent',
            color: tab === t.key ? 'var(--accent)' : 'var(--text2)',
            borderBottom: tab === t.key ? '2px solid var(--accent)' : '2px solid transparent',
          }}>{t.label}</button>
        ))}
      </div>

      {/* Main */}
      <main style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
        {loading && <div style={{ color: 'var(--text2)', textAlign: 'center', padding: 60 }}>載入中…</div>}

        {!loading && tab === TAB.SALES && (
          <>
            {/* KPI row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
              <KpiCard label='總銷售額' value={Math.round(summary?.total_amount || 0)} unit='NT$' />
              <KpiCard label='總銷售量' value={summary?.total_qty || 0} unit='件' />
              <KpiCard label='品項數' value={summary?.product_count || 0} unit='項' />
              <KpiCard label='品牌數' value={summary?.brand_count || 0} unit='個' />
            </div>

            {/* Monthly trend */}
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, marginBottom: 20 }}>
              <MonthlyChart data={[...monthly, ...prevMonthly]} title='月度銷售趨勢（與去年比較）' />
            </div>

            {/* Brand + Channel row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
                <BrandChart data={byBrand} title='品牌銷售排行（金額）' />
              </div>
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
                <ChannelPie data={byChannel} title='通路佔比' />
              </div>
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
              <BrandChart data={byBrand} title='品牌銷售排行（數量）' valueKey='qty' />
            </div>
          </>
        )}

        {!loading && tab === TAB.PURCHASE && (
          <div style={{ color: 'var(--text2)', textAlign: 'center', padding: 60 }}>
            採購資料將從 Google Sheets 同步後顯示。<br />
            請點擊右上角「資料同步 → Google Sheets」。
          </div>
        )}
      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={() => { setShowUpload(false); loadData() }}
        />
      )}

      <footer style={{ padding: '10px 24px', borderTop: '1px solid var(--border)', color: 'var(--text2)', fontSize: 11, display: 'flex', justifyContent: 'space-between' }}>
        <span>資料來源：ECOUNT ERP + Google Sheets</span>
        <span>每日 06:00 自動同步</span>
      </footer>
    </div>
  )
}
