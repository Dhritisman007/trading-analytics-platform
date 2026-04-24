// src/components/charts/FIIDIIChart.jsx

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import { formatChartDate, formatNumber } from '../../utils/formatters'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background:   'var(--color-background-primary)',
      border:       '0.5px solid var(--color-border-tertiary)',
      borderRadius: 'var(--border-radius-md)',
      padding:      '8px 12px',
      fontSize:     '11px',
    }}>
      <p style={{ margin: '0 0 5px', color: 'var(--color-text-secondary)' }}>
        {formatChartDate(label)}
      </p>
      {payload.map((entry) => (
        <p key={entry.name} style={{
          margin:     '2px 0',
          fontWeight: '500',
          color:      parseFloat(entry.value) >= 0 ? '#1D9E75' : '#E24B4A',
        }}>
          {entry.name}: {parseFloat(entry.value) >= 0 ? '+' : ''}
          {formatNumber(entry.value)} Cr
        </p>
      ))}
    </div>
  )
}

export default function FIIDIIChart({ chartData, height = 220 }) {
  if (!chartData?.dates?.length) return null

  // Combine into recharts format
  const data = chartData.dates.map((date, i) => ({
    date,
    FII: parseFloat(chartData.fii_net[i])  || 0,
    DII: parseFloat(chartData.dii_net[i])  || 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        margin={{ top: 5, right: 10, left: 10, bottom: 0 }}
        barCategoryGap="20%"
        barGap={2}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--color-border-tertiary)"
          strokeOpacity={0.5}
        />
        <XAxis
          dataKey="date"
          tickFormatter={formatChartDate}
          tick={{ fontSize: 9, fill: 'var(--color-text-tertiary)' }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={(v) => `${v > 0 ? '+' : ''}${(v / 1000).toFixed(0)}k`}
          tick={{ fontSize: 9, fill: 'var(--color-text-tertiary)' }}
          tickLine={false}
          axisLine={false}
          width={44}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke="var(--color-border-secondary)" strokeWidth={1} />
        <Legend
          wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
          iconType="square"
          iconSize={8}
        />
        <Bar
          dataKey="FII"
          fill="#1D9E75"
          radius={[2, 2, 0, 0]}
          // Color each bar based on value
          cell={(entry) => ({
            fill: entry.FII >= 0 ? '#1D9E75' : '#E24B4A',
          })}
        />
        <Bar
          dataKey="DII"
          fill="#378ADD"
          radius={[2, 2, 0, 0]}
          cell={(entry) => ({
            fill: entry.DII >= 0 ? '#378ADD' : '#B5D4F4',
          })}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}