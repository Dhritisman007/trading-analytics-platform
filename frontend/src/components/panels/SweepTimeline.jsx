// src/components/panels/SweepTimeline.jsx

import { formatDate } from '../../utils/formatters'

export default function SweepTimeline({ sweeps = [] }) {
  if (!sweeps.length) {
    return (
      <div style={{
        textAlign: 'center',
        padding:   '2rem',
        color:     'var(--color-text-tertiary)',
        fontSize:  '12px',
      }}>
        No liquidity sweeps detected in this period
      </div>
    )
  }

  return (
    <div style={{ position: 'relative' }}>
      {/* Vertical timeline line */}
      <div style={{
        position:   'absolute',
        left:       '14px',
        top:        '8px',
        bottom:     '8px',
        width:      '1px',
        background: 'var(--color-border-tertiary)',
      }} />

      {sweeps.map((sweep, i) => {
        const isBull      = sweep.type === 'bullish'
        const color       = isBull ? '#1D9E75' : '#E24B4A'
        const isHighVol   = sweep.high_volume

        return (
          <div key={i} style={{
            display:      'flex',
            gap:          '12px',
            marginBottom: '12px',
            position:     'relative',
          }}>
            {/* Timeline dot */}
            <div style={{
              width:        '28px',
              flexShrink:   0,
              display:      'flex',
              alignItems:   'flex-start',
              paddingTop:   '2px',
            }}>
              <div style={{
                width:        '12px',
                height:       '12px',
                borderRadius: '50%',
                background:   isHighVol ? color : `${color}60`,
                border:       `2px solid ${color}`,
                display:      'flex',
                alignItems:   'center',
                justifyContent: 'center',
                fontSize:     '7px',
                color:        '#fff',
                flexShrink:   0,
                zIndex:       1,
              }}>
                {isBull ? '▲' : '▼'}
              </div>
            </div>

            {/* Content */}
            <div style={{
              flex:         1,
              background:   `${color}08`,
              border:       `0.5px solid ${color}25`,
              borderRadius: 'var(--border-radius-md)',
              padding:      '8px 12px',
            }}>
              {/* Header row */}
              <div style={{
                display:        'flex',
                justifyContent: 'space-between',
                alignItems:     'center',
                marginBottom:   '5px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{
                    fontSize:   '12px',
                    fontWeight: '600',
                    color,
                  }}>
                    {isBull ? '↑ Bullish' : '↓ Bearish'} Sweep
                  </span>
                  {isHighVol && (
                    <span style={{
                      fontSize:     '9px',
                      fontWeight:   '600',
                      padding:      '1px 6px',
                      borderRadius: '20px',
                      background:   `${color}20`,
                      color,
                    }}>
                      ⚡ High volume
                    </span>
                  )}
                </div>
                <span style={{
                  fontSize: '10px',
                  color:    'var(--color-text-tertiary)',
                }}>
                  {formatDate(sweep.date)}
                </span>
              </div>

              {/* Price levels grid */}
              <div style={{
                display:             'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap:                 '8px',
                marginBottom:        '8px',
              }}>
                {[
                  {
                    label: 'Swept level',
                    value: `₹${sweep.swept_level}`,
                    color,
                  },
                  {
                    label: isBull ? 'Sweep low'   : 'Sweep high',
                    value: `₹${isBull ? sweep.sweep_low : sweep.sweep_high}`,
                    color: isBull ? '#E24B4A' : '#1D9E75',
                  },
                  {
                    label: 'Close',
                    value: `₹${sweep.close}`,
                    color: 'var(--color-text-primary)',
                  },
                ].map(({ label, value, color: c }) => (
                  <div key={label}>
                    <p style={{
                      fontSize: '9px',
                      color:    'var(--color-text-tertiary)',
                      margin:   '0 0 1px',
                    }}>
                      {label}
                    </p>
                    <p style={{
                      fontSize:   '12px',
                      fontWeight: '500',
                      color:      c,
                      margin:     0,
                    }}>
                      {value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Stats row */}
              <div style={{
                display:  'flex',
                gap:      '12px',
                fontSize: '10px',
                color:    'var(--color-text-secondary)',
              }}>
                <span>
                  Wick: <strong>{sweep.wick_pct}%</strong> of candle
                </span>
                <span>
                  Volume: <strong
                    style={{ color: parseFloat(sweep.vol_ratio) > 1.5 ? color : 'inherit' }}
                  >
                    {sweep.vol_ratio}×
                  </strong> avg
                </span>
                <span>
                  Recovery: <strong>{sweep.recovery_pct}%</strong>
                </span>
              </div>

              {/* Description */}
              <p style={{
                fontSize:   '11px',
                color:      'var(--color-text-secondary)',
                margin:     '6px 0 0',
                lineHeight: '1.5',
              }}>
                {sweep.description}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
