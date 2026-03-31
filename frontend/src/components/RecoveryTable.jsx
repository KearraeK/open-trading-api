export default function RecoveryTable({ data, currentDrawdown, recoveryThreshold }) {
  const currentAbs = Math.abs(currentDrawdown)

  const isCurrentBucket = (row, i, arr) => {
    const prevThr = i > 0 ? arr[i - 1].drawdown_threshold : -0.001
    return currentAbs > prevThr && currentAbs <= row.drawdown_threshold
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-bold text-slate-600 mb-4">④ 회복률 상세 테이블</h3>
      <div className="overflow-auto max-h-64 rounded-lg border border-slate-100">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-50 z-10">
            <tr>
              <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500">낙폭 구간</th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500">해당 일수</th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500">회복률</th>
              <th className="text-center py-2 px-3 text-xs font-semibold text-slate-500">상태</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => {
              const isCurrent = isCurrentBucket(row, i, data)
              const isBuyZone = row.recovery_rate <= recoveryThreshold
              return (
                <tr
                  key={i}
                  className={`border-t border-slate-50 ${
                    isCurrent ? 'bg-blue-50' : 'hover:bg-slate-50'
                  }`}
                >
                  <td className="py-2 px-3 text-slate-700 font-medium">
                    {`-${row.drawdown_threshold}% 이내`}
                    {isCurrent && (
                      <span className="ml-2 text-xs font-bold text-blue-600">← 현재</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-500">
                    {row.days_within.toLocaleString()}
                  </td>
                  <td
                    className={`py-2 px-3 text-right font-semibold ${
                      isBuyZone ? 'text-green-600' : 'text-slate-800'
                    }`}
                  >
                    {row.recovery_rate.toFixed(1)}%
                  </td>
                  <td className="py-2 px-3 text-center">
                    {isBuyZone && (
                      <span className="text-xs bg-green-100 text-green-700 font-semibold px-2 py-0.5 rounded-full">
                        매수구간
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
