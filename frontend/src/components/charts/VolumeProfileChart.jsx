// src/components/charts/VolumeProfileChart.jsx

export default function VolumeProfileChart({
  histogram = [],
  poc,
  vah,
  val,
  currentPrice,
  height = 500,
}) {
  if (!histogram.length) return null

  // Sort price low → high for display (bottom to top)
  const sorted = [...histogram].sort(
    (a, b) => parseFloat(a.price) - parseFloat(b.price)
  )
  const maxVol = Math.max(...sorted.map((b) => b.volume_pct))

  return (
    <div style={{ position: 'relative', height, overflowY: 'auto' }}>
      {sorted.map((bar, i) => {
        const price    = parseFloat(bar.price)
        const barColor = bar.is_poc  ? '#BA7517'  :
                         bar.is_vah  ? '#378ADD'  :
                         bar.is_val  ? '#7F77DD'  :
                         bar.in_va   ? '#378ADD40' : '#B4B2A960'

        const isNearPrice =
          currentPrice &&
          Math.abs(price - parseFloat(currentPrice)) / parseFloat(currentPrice) < 0.002

        return (
          <div
            key={i}
            style={{
              display:        'flex',
              alignItems:     'center',
              gap:            '8px',
              marginBottom:   '1px',
              padding:        '0 4px',
              background:     isNearPrice ? 'var(--color-background-tertiary)' : 'transparent',
              borderRadius:   '2px',
            }}
          >
            {/* Price label */}
            <span style={{
              fontSize:   '9px',
              color:      bar.is_poc ? '#BA7517' :
                          bar.is_vah ? '#378ADD' :
                          bar.is_val ? '#7F77DD' :
                          'var(--color-text-tertiary)',
              fontWeight: (bar.is_poc || bar.is_vah || bar.is_val) ? '600' : '400',
              width:      '60px',
              textAlign:  'right',
              flexShrink: 0,
            }}>
              ₹{bar.price}
              {bar.is_poc && ' POC'}
              {bar.is_vah && ' VAH'}
              {bar.is_val && ' VAL'}
            </span>

            {/* Bar */}
            <div style={{
              flex:      1,
              height:    '10px',
              position:  'relative',
            }}>
              <div style={{
                width:        `${(bar.volume_pct / maxVol) * 100}%`,
                height:       '100%',
                background:   barColor,
                borderRadius: '0 2px 2px 0',
                transition:   'width 0.5s ease-out',
                minWidth:     '2px',
              }} />
            </div>

            {/* Volume pct */}
            <span style={{
              fontSize:   '9px',
              color:      'var(--color-text-tertiary)',
              width:      '30px',
              flexShrink: 0,
            }}>
              {bar.volume_pct}%
            </span>
          </div>
        )
      })}
    </div>
  )
}
