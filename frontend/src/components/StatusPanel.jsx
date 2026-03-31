export default function StatusPanel({ result }) {
  const {
    ticker, current_price, peak_price,
    current_drawdown, recovery_rate_at_current,
    recovery_threshold, recovery_threshold_dd,
    mdd_condition,
    current_vix, vix_threshold, vix_condition,
    fear_greed_value, fear_greed_class, fear_greed_condition,
    buy_signal,
    analysis_start, analysis_end, total_days,
  } = result

  const remaining = (recovery_threshold_dd + current_drawdown).toFixed(1)

  return (
    <div
      className={`rounded-xl shadow-sm border-2 p-5 transition-colors ${
        buy_signal
          ? 'bg-green-50 border-green-400'
          : 'bg-white border-slate-200'
      }`}
    >
      {/* 헤더 */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{ticker}</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {analysis_start} ~ {analysis_end}&nbsp;&nbsp;(총 {total_days.toLocaleString()}일)
          </p>
        </div>
        <span
          className={`px-4 py-1.5 rounded-full text-sm font-bold whitespace-nowrap ${
            buy_signal
              ? 'bg-green-500 text-white shadow'
              : 'bg-slate-200 text-slate-600'
          }`}
        >
          {buy_signal ? '🟢 기계적 추가 매수 구간' : '⏳ 조건 미충족'}
        </span>
      </div>

      {/* 메트릭 카드 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-5">
        <MetricCard label="현재가" value={`$${current_price.toLocaleString()}`} />
        <MetricCard label="전고점" value={`$${peak_price.toLocaleString()}`} />
        <MetricCard
          label="현재 낙폭"
          value={`${current_drawdown.toFixed(2)}%`}
          valueColor={
            current_drawdown < -30 ? 'text-red-600'
            : current_drawdown < -15 ? 'text-orange-500'
            : 'text-slate-800'
          }
        />
        <MetricCard
          label="현재 회복률"
          value={`${recovery_rate_at_current.toFixed(1)}%`}
          sub={`기준: ${recovery_threshold}%`}
          badge={mdd_condition ? { text: 'MDD 충족 ✔', color: 'bg-green-100 text-green-700' } : null}
        />
        {current_vix !== null && (
          <MetricCard
            label="VIX"
            value={current_vix.toFixed(1)}
            sub={`기준: ${vix_threshold}`}
            valueColor={vix_condition ? 'text-red-600' : 'text-slate-800'}
            badge={vix_condition ? { text: '⚠ 공포', color: 'bg-red-100 text-red-700' } : null}
          />
        )}
        {fear_greed_value !== null && (
          <MetricCard
            label="공포탐욕지수"
            value={fear_greed_value}
            sub={fear_greed_class}
            valueColor={fear_greed_condition ? 'text-red-600' : 'text-slate-800'}
            badge={fear_greed_condition ? { text: '⚠ 공포', color: 'bg-red-100 text-red-700' } : null}
          />
        )}
      </div>

      {/* 힌트 메시지 */}
      <div className="mt-4 text-xs text-slate-600 bg-slate-50 rounded-lg px-4 py-2.5">
        💡 회복률&nbsp;<strong>{recovery_threshold}%</strong>&nbsp;기준 낙폭 레벨:
        &nbsp;<strong>-{recovery_threshold_dd.toFixed(1)}%</strong>&nbsp;&mdash;&nbsp;
        {Number(remaining) >= 0
          ? `현재에서 ${remaining}% 더 하락하면 매수 구간 진입`
          : `현재 매수 구간 돌파 (다시 ${Math.abs(Number(remaining)).toFixed(1)}% 상승시 탈절)`
        }
      </div>
    </div>
  )
}

function MetricCard({ label, value, sub, valueColor = 'text-slate-800', badge }) {
  return (
    <div className="bg-white rounded-lg border border-slate-100 shadow-sm p-3">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-bold mt-0.5 ${valueColor}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      {badge && (
        <span className={`inline-block mt-1 text-xs font-semibold px-2 py-0.5 rounded-full ${badge.color}`}>
          {badge.text}
        </span>
      )}
    </div>
  )
}
