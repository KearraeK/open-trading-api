import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

const fmtDate = (str) => {
  const d = new Date(str)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function DrawdownChart({ data, recoveryThresholdDd, currentDrawdown }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-bold text-slate-600 mb-4">② MDD 낙폭 추이</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 40, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="date"
            tickFormatter={fmtDate}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            tickFormatter={(v) => `${v}%`}
            width={45}
          />
          <Tooltip
            labelFormatter={(v) => `날짜: ${v}`}
            formatter={(v) => [`${v.toFixed(2)}%`, '낙폭']}
            contentStyle={{ fontSize: 12 }}
          />

          {/* 주요 기준선 */}
          {[-10, -20, -30, -40, -50].map((lvl) => (
            <ReferenceLine
              key={lvl} y={lvl}
              stroke="#e2e8f0" strokeDasharray="4 3"
              label={{ value: `${lvl}%`, position: 'right', fontSize: 9, fill: '#94a3b8' }}
            />
          ))}

          {/* 회복률 80% 기준 낙폭 선 */}
          <ReferenceLine
            y={-recoveryThresholdDd}
            stroke="#f59e0b" strokeDasharray="5 4" strokeWidth={1.5}
            label={{ value: `매수기준 -${recoveryThresholdDd.toFixed(0)}%`, position: 'right', fontSize: 9, fill: '#f59e0b' }}
          />

          {/* 현재 낙폭 */}
          <ReferenceLine
            y={currentDrawdown}
            stroke="#1d4ed8" strokeWidth={1.5} strokeDasharray="3 3"
            label={{ value: `현재 ${currentDrawdown.toFixed(1)}%`, position: 'right', fontSize: 9, fill: '#1d4ed8' }}
          />

          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="#ef4444"
            fill="url(#ddGrad)"
            strokeWidth={1}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
