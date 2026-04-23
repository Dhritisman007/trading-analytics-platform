// src/components/charts/EquityCurveChart.jsx

import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { formatPrice, formatChartDate } from '../../utils/formatters'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const value = payload[0]?.value
  return (
    <div style={{
      background:   'var(--color-background-primary)',
      border:       '0.5px solid var(--color-border-tertiary)',
      borderRadius: 'var(--border-radius-md)',
      padding:      '8px 12px',
      fontSize:     '11px',
    }}>
      <p style={{ margin: '0 0 3px', color: 'var(--color-text-secondary)' }}>
        {formatChartDate(label)}
      </p>
      <p style={{ margin: 0, fontWeight: '500', color: 'var(--color-text-primary)' }}>
        {formatPrice(value)}
      </p>
    </div>
  )
}

export default function EquityCurveChart({
  data          = [],
  initialCapital = 100000,
  height         = 220,
}) {
  if (!data.length) return null

  const finalValue = data[data.length - 1]?.value || initialCapital
  const isProfit   = finalValue >= initialCapital
  const color      = isProfit ? '#1D9E75' : '#E24B4A'

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={data}
        margin={{ top: 10, right: 10, left: 10, bottom: 0 }}
      >
        <defs>
          <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor={color} stopOpacity={0.2} />
            <stop offset="95%" stopColor={color} stopOpacity={0}   />
          </linearGradient>
        </defs>

        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--color-border-tertiary)"
          strokeOpacity={0.5}
        />

        <XAxis
          dataKey="date"
          tickFormatter={formatChartDate}
          tick={{ fontSize: 10, fill: 'var(--color-text-tertiary)' }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />

        <YAxis
          tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
          tick={{ fontSize: 10, fill: 'var(--color-text-tertiary)' }}
          tickLine={false}
          axisLine={false}
          width={50}
        />

        <Tooltip content={<CustomTooltip />} />

        {/* Initial capital reference line */}
        <ReferenceLine
          y={initialCapital}
          stroke="var(--color-text-tertiary)"
          strokeDasharray="4 3"
          strokeWidth={1}
        />

        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          fill="url(#equityGradient)"
          dot={false}
          activeDot={{ r: 3, fill: color }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}