// src/components/charts/StochRSIChart.jsx

import {
    ComposedChart, Line, XAxis, YAxis,
    CartesianGrid, Tooltip, ReferenceLine,
    ResponsiveContainer, Legend,
} from 'recharts'
import { formatChartDate } from '../../utils/formatters'

export default function StochRSIChart({ data = [], height = 140 }) {
    const validData = data
        .filter((d) => d.stoch_k != null && d.stoch_d != null)
        .slice(-60)  // last 60 candles

    if (!validData.length) return null

    return (
        <ResponsiveContainer width="100%" height={height}>
            <ComposedChart
                data={validData}
                margin={{ top: 5, right: 10, left: 0, bottom: 0 }}
            >
                <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--color-border-tertiary)"
                    strokeOpacity={0.5}
                    vertical={false}
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
                    domain={[0, 100]}
                    tick={{ fontSize: 9, fill: 'var(--color-text-tertiary)' }}
                    tickLine={false}
                    axisLine={false}
                    width={25}
                    ticks={[0, 20, 50, 80, 100]}
                />
                <Tooltip
                    contentStyle={{
                        background: 'var(--color-background-primary)',
                        border: '0.5px solid var(--color-border-tertiary)',
                        borderRadius: '6px',
                        fontSize: '11px',
                    }}
                    formatter={(val, name) => [parseFloat(val).toFixed(1), name]}
                    labelFormatter={formatChartDate}
                />

                {/* Overbought / oversold zones */}
                <ReferenceLine y={80} stroke="#E24B4A" strokeDasharray="4 3" strokeWidth={1} />
                <ReferenceLine y={20} stroke="#1D9E75" strokeDasharray="4 3" strokeWidth={1} />
                <ReferenceLine y={50} stroke="var(--color-border-secondary)" strokeWidth={0.5} />

                <Line
                    type="monotone"
                    dataKey="stoch_k"
                    name="%K"
                    stroke="#7F77DD"
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 3 }}
                />
                <Line
                    type="monotone"
                    dataKey="stoch_d"
                    name="%D"
                    stroke="#BA7517"
                    strokeWidth={1}
                    dot={false}
                    activeDot={{ r: 3 }}
                />
            </ComposedChart>
        </ResponsiveContainer>
    )
}