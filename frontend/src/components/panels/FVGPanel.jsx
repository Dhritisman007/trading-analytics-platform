// src/components/panels/FVGPanel.jsx

import { useState }  from 'react'
import { useQuery }  from '@tanstack/react-query'
import { fvgApi }    from '../../api/endpoints'
import { formatPrice, formatNumber, formatDate } from '../../utils/formatters'
import { LoadingSpinner } from '../ui/LoadingSpinner'
import { ErrorMessage }   from '../ui/ErrorMessage'

const StrengthDot = ({ strength }) => {
  const colors = {
    strong: '#1D9E75',
    medium: '#BA7517',
    weak:   '#888780',
  }
  return (
    <span style={{
      display:      'inline-flex',
      alignItems:   'center',
      gap:          '4px',
      fontSize:     '10px',
      color:        colors[strength] || '#888780',
      fontWeight:   '500',
    }}>
      <span style={{
        width:        '6px',
        height:       '6px',
        borderRadius: '50%',
        background:   colors[strength] || '#888780',
        display:      'inline-block',
      }} />
      {strength}
    </span>
  )
}

const FVGRow = ({ fvg, latestPrice }) => {
  const isBull    = fvg.type === 'bullish'
  const isFilled  = fvg.filled
  const midpoint  = (fvg.gap_top + fvg.gap_bottom) / 2
  const distance  = latestPrice ? Math.abs(latestPrice - midpoint) : null
  const distPct   = latestPrice
    ? formatNumber(Math.abs(latestPrice - midpoint) / latestPrice * 100)
    : null

  return (
    <div style={{
      display:      'flex',
      alignItems:   'center',
      gap:          '10px',
      padding:      '8px 10px',
      borderRadius: 'var(--border-radius-md)',
      background:   isFilled
        ? 'var(--color-background-secondary)'
        : isBull
        ? '#E1F5EE18'
        : '#FCEBEB18',
      border: `0.5px solid ${
        isFilled  ? 'var(--color-border-tertiary)'
        : isBull  ? '#1D9E7530'
        : '#E24B4A30'
      }`,
      marginBottom: '6px',
      opacity:      isFilled ? 0.6 : 1,
    }}>
      {/* Type indicator */}
      <div style={{
        width:        '3px',
        height:       '36px',
        borderRadius: '2px',
        background:   isFilled ? '#888780' : isBull ? '#1D9E75' : '#E24B4A',
        flexShrink:   0,
      }} />

      {/* Main info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          display:     'flex',
          alignItems:  'center',
          gap:         '6px',
          marginBottom: '3px',
        }}>
          <span style={{
            fontSize:   '11px',
            fontWeight: '500',
            color:      isBull ? '#1D9E75' : '#E24B4A',
          }}>
            {isBull ? '↑ Bullish' : '↓ Bearish'}
          </span>
          <StrengthDot strength={fvg.strength} />
          {isFilled && (
            <span style={{
              fontSize:     '9px',
              padding:      '1px 5px',
              borderRadius: '20px',
              background:   '#F1EFE8',
              color:        '#888780',
            }}>
              filled
            </span>
          )}
        </div>

        <div style={{
          fontSize: '11px',
          color:    'var(--color-text-secondary)',
        }}>
          {formatPrice(fvg.gap_bottom)} → {formatPrice(fvg.gap_top)}
          <span style={{ marginLeft: '6px', color: 'var(--color-text-tertiary)' }}>
            ({formatNumber(fvg.gap_size_pct)}%)
          </span>
        </div>
      </div>

      {/* Distance to price */}
      {distance != null && !isFilled && (
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <p style={{
            fontSize:   '11px',
            fontWeight: '500',
            color:      'var(--color-text-primary)',
            margin:     '0 0 1px',
          }}>
            {distPct}% away
          </p>
          <p style={{
            fontSize: '10px',
            color:    'var(--color-text-tertiary)',
            margin:   0,
          }}>
            {formatDate(fvg.candle_3)}
          </p>
        </div>
      )}
    </div>
  )
}

export default function FVGPanel({ symbol = '^NSEI', period = '3mo', latestPrice }) {
  const [onlyOpen, setOnlyOpen] = useState(false)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey:  ['fvg', symbol, period, onlyOpen],
    queryFn:   () => fvgApi.getAll(symbol, period, onlyOpen),
    staleTime: 30 * 60 * 1000,
  })

  if (isLoading) return <LoadingSpinner size={20} />
  if (error)     return <ErrorMessage message={error.message} onRetry={refetch} />

  const summary  = data?.summary        || {}
  const fvgs     = data?.fvgs           || []
  const nearest  = data?.nearest_open_fvg

  return (
    <div>
      {/* Summary row */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap:                 '8px',
        marginBottom:        '12px',
      }}>
        {[
          { label: 'Total FVGs',  value: summary.total_fvgs },
          { label: 'Open',        value: summary.open,   color: '#1D9E75' },
          { label: 'Filled',      value: summary.filled, color: '#888780' },
          { label: 'Fill rate',   value: `${summary.fill_rate_pct}%` },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background:   'var(--color-background-secondary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-md)',
            padding:      '8px 10px',
            textAlign:    'center',
          }}>
            <p style={{
              fontSize: '10px',
              color:    'var(--color-text-tertiary)',
              margin:   '0 0 2px',
            }}>
              {label}
            </p>
            <p style={{
              fontSize:   '16px',
              fontWeight: '500',
              color:      color || 'var(--color-text-primary)',
              margin:     0,
            }}>
              {value ?? '—'}
            </p>
          </div>
        ))}
      </div>

      {/* Nearest open FVG highlight */}
      {nearest && (
        <div style={{
          background:   nearest.type === 'bullish' ? '#E1F5EE' : '#FCEBEB',
          border:       `1px solid ${nearest.type === 'bullish' ? '#1D9E75' : '#E24B4A'}40`,
          borderRadius: 'var(--border-radius-lg)',
          padding:      '10px 14px',
          marginBottom: '12px',
        }}>
          <p style={{
            fontSize:   '11px',
            fontWeight: '500',
            color:      nearest.type === 'bullish' ? '#085041' : '#791F1F',
            margin:     '0 0 4px',
          }}>
            Nearest open FVG — {nearest.type}
          </p>
          <p style={{
            fontSize: '12px',
            color:    'var(--color-text-secondary)',
            margin:   0,
          }}>
            Zone: {formatPrice(nearest.gap_bottom)} → {formatPrice(nearest.gap_top)} ·
            Size: {formatNumber(nearest.gap_size_pct)}% ·
            Strength: {nearest.strength}
          </p>
        </div>
      )}

      {/* Filter toggle */}
      <div style={{
        display:      'flex',
        gap:          '6px',
        marginBottom: '10px',
      }}>
        {[
          { label: 'All FVGs', val: false },
          { label: 'Open only', val: true },
        ].map(({ label, val }) => (
          <button
            key={String(val)}
            onClick={() => setOnlyOpen(val)}
            style={{
              fontSize:     '11px',
              padding:      '4px 12px',
              borderRadius: '20px',
              border:       '0.5px solid var(--color-border-tertiary)',
              background:   onlyOpen === val
                ? 'var(--color-text-primary)'
                : 'var(--color-background-secondary)',
              color: onlyOpen === val
                ? 'var(--color-background-primary)'
                : 'var(--color-text-secondary)',
              cursor:     'pointer',
              fontWeight: onlyOpen === val ? '500' : '400',
            }}
          >
            {label}
          </button>
        ))}
        <span style={{
          marginLeft: 'auto',
          fontSize:   '11px',
          color:      'var(--color-text-tertiary)',
          alignSelf:  'center',
        }}>
          {fvgs.length} gaps
        </span>
      </div>

      {/* FVG list */}
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {fvgs.length === 0 ? (
          <p style={{
            textAlign: 'center',
            padding:   '2rem',
            color:     'var(--color-text-tertiary)',
            fontSize:  '12px',
          }}>
            No FVGs found for this period
          </p>
        ) : (
          fvgs.map((fvg, i) => (
            <FVGRow
              key={i}
              fvg={fvg}
              latestPrice={latestPrice}
            />
          ))
        )}
      </div>
    </div>
  )
}