// src/pages/Dashboard.jsx
import { useMarket } from '../hooks/useMarket'
import { useLatestSignals } from '../hooks/useIndicators'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage }   from '../components/ui/ErrorMessage'
import { StatCard }       from '../components/ui/StatCard'
import { formatPrice, formatPct } from '../utils/formatters'

export default function Dashboard() {
  const { data: market, isLoading, error, refetch } = useMarket()
  const { data: signals } = useLatestSignals()

  if (isLoading) return <LoadingSpinner />
  if (error)     return <ErrorMessage message={error.message} onRetry={refetch} />

  const summary = market?.summary || {}
  const latest  = signals?.latest  || {}

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 4px' }}>
          Market Dashboard
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
          {market?.name} · {market?.period} · {market?.count} candles
        </p>
      </div>

      {/* Stat cards */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
        gap:                 '10px',
        marginBottom:        '1.5rem',
      }}>
        <StatCard
          label="Last Close"
          value={formatPrice(summary.latest_close)}
          change={summary.change_pct}
        />
        <StatCard
          label="Period High"
          value={formatPrice(summary.period_high)}
          color="#1D9E75"
        />
        <StatCard
          label="Period Low"
          value={formatPrice(summary.period_low)}
          color="#E24B4A"
        />
        <StatCard
          label="RSI"
          value={latest.rsi_value || '—'}
          unit=""
          color={
            latest.rsi_signal === 'overbought' ? '#E24B4A' :
            latest.rsi_signal === 'oversold'   ? '#1D9E75' :
            'var(--color-text-primary)'
          }
        />
        <StatCard
          label="Price vs EMA"
          value={latest.price_vs_ema || '—'}
          color={latest.price_vs_ema === 'above' ? '#1D9E75' : '#E24B4A'}
        />
      </div>

      {/* Placeholder for candlestick chart — Day 16 */}
      <div style={{
        height:       '400px',
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        display:      'flex',
        alignItems:   'center',
        justifyContent: 'center',
        color:        'var(--color-text-tertiary)',
        fontSize:     '13px',
      }}>
        Candlestick chart — building on Day 16
      </div>
    </div>
  )
}