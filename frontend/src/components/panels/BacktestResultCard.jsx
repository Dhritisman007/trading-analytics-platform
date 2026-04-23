// src/components/panels/BacktestResultCard.jsx

import { formatNumber, formatPrice } from '../../utils/formatters'
import EquityCurveChart from '../charts/EquityCurveChart'

const MetricPill = ({ label, value, color }) => (
  <div style={{
    background:   'var(--color-background-secondary)',
    border:       '0.5px solid var(--color-border-tertiary)',
    borderRadius: 'var(--border-radius-md)',
    padding:      '8px 12px',
    textAlign:    'center',
  }}>
    <p style={{
      fontSize: '10px',
      color:    'var(--color-text-secondary)',
      margin:   '0 0 3px',
    }}>
      {label}
    </p>
    <p style={{
      fontSize:   '15px',
      fontWeight: '500',
      color:      color || 'var(--color-text-primary)',
      margin:     0,
    }}>
      {value}
    </p>
  </div>
)

export default function BacktestResultCard({ result }) {
  if (!result) return null

  const perf  = result.performance  || {}
  const bh    = result.vs_buy_hold  || {}
  const grade = result.grade        || {}
  const cfg   = result.config       || {}

  const gradeColors = {
    A: '#1D9E75', B: '#5DCAA5',
    C: '#BA7517', D: '#E24B4A', F: '#791F1F',
  }
  const gradeColor = gradeColors[grade.grade] || '#888780'
  const returnPct  = parseFloat(perf.total_return_pct)
  const returnColor = returnPct >= 0 ? '#1D9E75' : '#E24B4A'

  return (
    <div>
      {/* Header strip */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        marginBottom:   '12px',
      }}>
        <div>
          <span style={{
            fontSize:     '13px',
            fontWeight:   '500',
            color:        'var(--color-text-primary)',
          }}>
            {result.description}
          </span>
          <span style={{
            fontSize:   '11px',
            color:      'var(--color-text-secondary)',
            marginLeft: '8px',
          }}>
            {cfg.data_start} → {cfg.data_end}
          </span>
        </div>
        <span style={{
          fontSize:     '18px',
          fontWeight:   '500',
          padding:      '4px 14px',
          borderRadius: '20px',
          background:   `${gradeColor}18`,
          color:        gradeColor,
        }}>
          {grade.grade}
        </span>
      </div>

      {/* Metric pills */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))',
        gap:                 '8px',
        marginBottom:        '14px',
      }}>
        <MetricPill
          label="Total return"
          value={`${returnPct >= 0 ? '+' : ''}${formatNumber(returnPct)}%`}
          color={returnColor}
        />
        <MetricPill
          label="Buy & hold"
          value={`${formatNumber(bh.buy_hold_return_pct)}%`}
        />
        <MetricPill
          label="Alpha"
          value={`${parseFloat(bh.alpha) >= 0 ? '+' : ''}${formatNumber(bh.alpha)}%`}
          color={parseFloat(bh.alpha) >= 0 ? '#1D9E75' : '#E24B4A'}
        />
        <MetricPill
          label="Sharpe ratio"
          value={formatNumber(perf.sharpe_ratio)}
          color={parseFloat(perf.sharpe_ratio) >= 1 ? '#1D9E75' : '#BA7517'}
        />
        <MetricPill
          label="Max drawdown"
          value={`${formatNumber(perf.max_drawdown_pct)}%`}
          color="#E24B4A"
        />
        <MetricPill
          label="Win rate"
          value={`${formatNumber(perf.win_rate_pct)}%`}
        />
        <MetricPill
          label="Profit factor"
          value={formatNumber(perf.profit_factor)}
          color={parseFloat(perf.profit_factor) >= 1.5 ? '#1D9E75' : '#BA7517'}
        />
        <MetricPill
          label="Total trades"
          value={result.total_trades}
        />
      </div>

      {/* Equity curve */}
      {result.equity_curve?.length > 0 && (
        <div style={{
          background:   'var(--color-background-secondary)',
          borderRadius: 'var(--border-radius-md)',
          padding:      '10px',
          marginBottom: '10px',
        }}>
          <p style={{
            fontSize:     '11px',
            fontWeight:   '500',
            color:        'var(--color-text-secondary)',
            margin:       '0 0 8px',
          }}>
            Equity curve
          </p>
          <EquityCurveChart
            data={result.equity_curve}
            initialCapital={cfg.initial_capital}
            height={200}
          />
        </div>
      )}

      {/* Outperformed badge */}
      <div style={{
        padding:      '8px 12px',
        background:   bh.outperformed ? '#E1F5EE' : '#FCEBEB',
        borderRadius: 'var(--border-radius-md)',
        fontSize:     '12px',
        color:        bh.outperformed ? '#085041' : '#791F1F',
        fontWeight:   '500',
      }}>
        {bh.outperformed
          ? `Strategy beat buy & hold by ${formatNumber(bh.alpha)}%`
          : `Strategy underperformed buy & hold by ${Math.abs(formatNumber(bh.alpha))}%`}
      </div>

      {/* Grade verdict */}
      <p style={{
        fontSize:   '12px',
        color:      gradeColor,
        margin:     '8px 0 0',
        fontWeight: '500',
      }}>
        {grade.verdict}
      </p>
    </div>
  )
}