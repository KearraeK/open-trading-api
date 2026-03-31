import { useState } from 'react'
import axios from 'axios'
import AnalyzerForm from './components/AnalyzerForm'
import StatusPanel from './components/StatusPanel'
import PriceChart from './components/PriceChart'
import DrawdownChart from './components/DrawdownChart'
import RecoveryRateChart from './components/RecoveryRateChart'
import RecoveryTable from './components/RecoveryTable'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export default function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const handleAnalyze = async (params) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.get(`${API_BASE}/api/analyze`, { params })
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message ?? '분석 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <span className="text-2xl">📈</span>
          <div>
            <h1 className="text-xl font-bold text-slate-800">VIX &amp; MDD 회복률 분석기</h1>
            <p className="text-xs text-slate-500 mt-0.5">역사적 MDD 데이터로 기계적 추가 매수 타이밍 산출</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-5">
        {/* 입력 폼 */}
        <AnalyzerForm onAnalyze={handleAnalyze} loading={loading} />

        {/* 로딩 */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-slate-500">데이터 수집 및 분석 중... (10초 전후 소요)</p>
          </div>
        )}

        {/* 에러 */}
        {!loading && error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* 결과 */}
        {!loading && result && (
          <>
            <StatusPanel result={result} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <PriceChart data={result.price_chart} ticker={result.ticker} />
              <DrawdownChart
                data={result.price_chart}
                recoveryThresholdDd={result.recovery_threshold_dd}
                currentDrawdown={result.current_drawdown}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <RecoveryRateChart
                data={result.recovery_table}
                recoveryThreshold={result.recovery_threshold}
                currentDrawdown={result.current_drawdown}
              />
              <RecoveryTable
                data={result.recovery_table}
                currentDrawdown={result.current_drawdown}
                recoveryThreshold={result.recovery_threshold}
              />
            </div>
          </>
        )}

        {/* 초기 안내 */}
        {!loading && !result && !error && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
            <span className="text-5xl">📊</span>
            <p className="text-sm">티커를 입력하고 ‘분석하기’를 눌러주세요</p>
          </div>
        )}
      </main>
    </div>
  )
}
