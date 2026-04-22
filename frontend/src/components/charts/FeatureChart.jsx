// src/components/charts/FeatureChart.jsx

export default function FeatureChart({ chartData, height = 280 }) {
  if (!chartData?.labels?.length) return null

  const { labels, contributions, colors } = chartData
  const maxAbs = Math.max(...contributions.map(Math.abs), 0.001)

  return (
    <div style={{ padding: '4px 0' }}>
      {labels.map((label, i) => {
        const value   = contributions[i]
        const color   = colors[i]
        const barPct  = Math.abs(value) / maxAbs * 100
        const isBull  = value >= 0

        return (
          <div key={label} style={{
            display:      'flex',
            alignItems:   'center',
            gap:          '8px',
            marginBottom: '8px',
            fontSize:     '11px',
          }}>
            {/* Label */}
            <div style={{
              width:      '160px',
              flexShrink: 0,
              color:      'var(--color-text-secondary)',
              textAlign:  'right',
              fontSize:   '11px',
            }}>
              {label}
            </div>

            {/* Bar container — split at centre */}
            <div style={{
              flex:       1,
              display:    'flex',
              alignItems: 'center',
              gap:        '2px',
              height:     '18px',
            }}>
              {/* Left side (bearish) */}
              <div style={{
                flex:           1,
                display:        'flex',
                justifyContent: 'flex-end',
              }}>
                {!isBull && (
                  <div style={{
                    width:        `${barPct}%`,
                    height:       '14px',
                    background:   '#E24B4A',
                    borderRadius: '2px 0 0 2px',
                    opacity:      0.8,
                  }} />
                )}
              </div>

              {/* Centre line */}
              <div style={{
                width:      '1px',
                height:     '18px',
                background: 'var(--color-border-secondary)',
                flexShrink: 0,
              }} />

              {/* Right side (bullish) */}
              <div style={{ flex: 1 }}>
                {isBull && (
                  <div style={{
                    width:        `${barPct}%`,
                    height:       '14px',
                    background:   '#1D9E75',
                    borderRadius: '0 2px 2px 0',
                    opacity:      0.8,
                  }} />
                )}
              </div>
            </div>

            {/* Value */}
            <div style={{
              width:      '50px',
              flexShrink: 0,
              color:      isBull ? '#1D9E75' : '#E24B4A',
              fontWeight: '500',
              fontSize:   '10px',
            }}>
              {isBull ? '+' : ''}{value?.toFixed ? value.toFixed(4) : value}
            </div>
          </div>
        )
      })}

      {/* Legend */}
      <div style={{
        display:        'flex',
        justifyContent: 'center',
        gap:            '20px',
        marginTop:      '10px',
        fontSize:       '11px',
        color:          'var(--color-text-secondary)',
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{
            width:        '12px', height: '3px',
            background:   '#E24B4A', display: 'inline-block',
          }} />
          Bearish push
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{
            width:        '12px', height: '3px',
            background:   '#1D9E75', display: 'inline-block',
          }} />
          Bullish push
        </span>
      </div>
    </div>
  )
}