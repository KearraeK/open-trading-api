import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

const fmtDate = (str) => {
  const d = new Date(str)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function PriceChart({ data, ticker }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h3 className="text-sm font-bold text-slate-600 mb-4">① 주가 추이 ({ticker})</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
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
            tickFormatter={(v) => `$${v}`}
            width={55}
          />
          <Tooltip
            labelFormatter={(v) => `날짜: ${v}`}
            formatter={(v) => [`$${v.toLocaleString()}`, '주가']}
            contentStyle={{ fontSize: 12 }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            fill="url(#priceGrad)"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
