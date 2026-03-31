import { useState } from 'react'

const DEFAULTS = {
  ticker: 'SPY',
  years: 20,
  recovery_threshold: 80,
  vix_threshold: 30,
  no_vix: false,
  no_fear_greed: false,
  step: 5,
  demo: true,
}

const QUICK_TICKERS = ['SPY', 'QQQ', 'IWM', 'AAPL', 'TSLA', 'NVDA']

export default function AnalyzerForm({ onAnalyze, loading }) {
  const [p, setP] = useState(DEFAULTS)
  const set = (k, v) => setP((prev) => ({ ...prev, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    onAnalyze(p)
  }

  const inputCls =
    'w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
  const labelCls = 'block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide'

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow-sm border border-slate-200 p-5"
    >
      <h2 className="text-sm font-bold text-slate-600 mb-4">분석 설정</h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
        {/* 티커 */}
        <div className="col-span-2 sm:col-span-1">
          <label className={labelCls}>티커</label>
          <input
            type="text"
            value={p.ticker}
            onChange={(e) => set('ticker', e.target.value.toUpperCase())}
            placeholder="SPY, QQQ..."
            className={inputCls}
            required
          />
        </div>

        {/* 분석기간 */}
        <div>
          <label className={labelCls}>분석기간 (년)</label>
          <input
            type="number" min={1} max={40}
            value={p.years}
            onChange={(e) => set('years', Number(e.target.value))}
            className={inputCls}
          />
        </div>

        {/* 회복률 기준 */}
        <div>
          <label className={labelCls}>회복률 기준 (%)</label>
          <input
            type="number" min={50} max={99} step={5}
            value={p.recovery_threshold}
            onChange={(e) => set('recovery_threshold', Number(e.target.value))}
            className={inputCls}
          />
        </div>

        {/* VIX 기준 */}
        <div>
          <label className={labelCls}>VIX 기준</label>
          <input
            type="number" min={10} max={80} step={1}
            value={p.vix_threshold}
            onChange={(e) => set('vix_threshold', Number(e.target.value))}
            className={inputCls}
          />
        </div>

        {/* 구간 간격 */}
        <div>
          <label className={labelCls}>구간 간격 (%)</label>
          <input
            type="number" min={1} max={10} step={1}
            value={p.step}
            onChange={(e) => set('step', Number(e.target.value))}
            className={inputCls}
          />
        </div>

        {/* 토글 */}
        <div className="flex flex-col justify-end gap-2 pb-0.5">
          <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
            <input
              type="checkbox" checked={p.no_vix}
              onChange={(e) => set('no_vix', e.target.checked)}
              className="rounded"
            />
            VIX 제외
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
            <input
              type="checkbox" checked={p.no_fear_greed}
              onChange={(e) => set('no_fear_greed', e.target.checked)}
              className="rounded"
            />
            공포탐욕 제외
          </label>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox" checked={p.demo}
              onChange={(e) => set('demo', e.target.checked)}
              className="rounded accent-amber-500"
            />
            <span className="text-amber-600 font-semibold">데모 모드</span>
          </label>
        </div>
      </div>

      {/* 버튼대 */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={loading || !p.ticker}
          className="px-5 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '분석 중...' : '분석하기'}
        </button>

        <span className="text-xs text-slate-400">빠른 선택:</span>
        {QUICK_TICKERS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => set('ticker', t)}
            className={`px-3 py-1 text-xs rounded-md border transition-colors ${
              p.ticker === t
                ? 'bg-blue-100 border-blue-400 text-blue-700 font-semibold'
                : 'border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
    </form>
  )
}
