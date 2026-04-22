// src/components/panels/CategoryBreakdown.jsx

export default function CategoryBreakdown({ categorySummary }) {
  if (!categorySummary) return null

  const entries = Object.entries(categorySummary)
  if (!entries.length) return null

  const maxImpact = Math.max(...entries.map(([, v]) => v.total_impact))

  const categoryColors = {
    RSI:    '#7F77DD',
    EMA:    '#378ADD',
    MACD:   '#BA7517',
    Price:  '#1D9E75',
    Volume: '#888780',
    ATR:    '#D85A30',
  }

  return (
    <div>
      {entries.map(([category, data]) => {
        const barPct  = (data.total_impact / maxImpact) * 100
        const isBull  = data.net_direction === 'bullish'
        const color   = categoryColors[category] || '#888780'

        return (
          <div key={category} style={{ marginBottom: '10px' }}>
            <div style={{
              display:        'flex',
              justifyContent: 'space-between',
              alignItems:     'center',
              marginBottom:   '4px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{
                  width:        '8px',
                  height:       '8px',
                  borderRadius: '50%',
                  background:   color,
                  display:      'inline-block',
                }} />
                <span style={{
                  fontSize:   '12px',
                  fontWeight: '500',
                  color:      'var(--color-text-primary)',
                }}>
                  {category}
                </span>
                <span style={{
                  fontSize: '10px',
                  color:    'var(--color-text-tertiary)',
                }}>
                  {data.feature_count} feature{data.feature_count !== 1 ? 's' : ''}
                </span>
              </div>

              <span style={{
                fontSize:     '11px',
                fontWeight:   '500',
                padding:      '2px 8px',
                borderRadius: '20px',
                background:   isBull ? '#E1F5EE' : '#FCEBEB',
                color:        isBull ? '#085041' : '#791F1F',
              }}>
                {data.net_direction}
              </span>
            </div>

            {/* Impact bar */}
            <div style={{
              height:       '6px',
              background:   'var(--color-background-secondary)',
              borderRadius: '3px',
              overflow:     'hidden',
            }}>
              <div style={{
                width:        `${barPct}%`,
                height:       '100%',
                background:   color,
                borderRadius: '3px',
                opacity:      0.75,
                transition:   'width 0.8s ease-out',
              }} />
            </div>

            <p style={{
              fontSize:  '10px',
              color:     'var(--color-text-tertiary)',
              margin:    '3px 0 0',
            }}>
              Top: {data.top_feature}
            </p>
          </div>
        )
      })}
    </div>
  )
}