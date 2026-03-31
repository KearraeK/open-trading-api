import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'

export default function RecoveryRateChart({ data, recoveryThreshold, currentDrawdown }) {
  const currentAbs = Math.abs(currentDrawdown)

  const barColor = (entry) => {
    if (entry.drawdown_threshold >= currentAbs - 0.1) {
      // 현재 낙폭 지점 및 그 이후
      return entry.recovery_rate <= recoveryThreshold ? '#22c55e' : '#93c5fd'
    }
    return '#3b82f6'
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-bold text-slate-600 mb-4">③ 구간별 회복률</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 10, right: 40, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="drawdown_threshold"
            tickFormatter={(v) => `-${v}%`}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
          />
          <YAxis
            domain={[0, 105]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            width={40}
          />
          <Tooltip
            formatter={(v) => [`${Number(v).toFixed(1)}%`, '회복률']}
            labelFormatter={(v) => `낙폭 ${v}% 이내`}
            contentStyle={{ fontSize: 12 }}
          />
          {/* 기준선 */}
          <ReferenceLine
            y={recoveryThreshold}
            stroke="#f59e0b" strokeDasharray="5 4" strokeWidth={1.5}
            label={{ value: `기준 ${recoveryThreshold}%`, position: 'right', fontSize: 9, fill: '#f59e0b' }}
          />
          {/* 현재 낙폭 */}
          <ReferenceLine
            x={Math.round(currentAbs / 5) * 5}
            stroke="#1d4ed8" strokeDasharray="3 3" strokeWidth={1.5}
            label={{ value: '현재', position: 'top', fontSize: 9, fill: '#1d4ed8' }}
          />
          <Bar dataKey="recovery_rate" radius={[3, 3, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={barColor(entry)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-500 inline-block" />지난 기간</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-300 inline-block" />현재 이후 (조건 미충족)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500 inline-block" />매수 구간</span>
      </div>
    </div>
  )
}
