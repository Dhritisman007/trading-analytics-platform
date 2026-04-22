// src/components/ui/ConfidenceBar.jsx

export default function ConfidenceBar({
  confidence = 0,
  signal     = 'BUY',
  strength   = 'moderate',
}) {
  const isBuy    = signal === 'BUY'
  const barColor = isBuy ? '#1D9E75' : '#E24B4A'

  const strengthLabel = {
    strong:   { label: 'Strong signal',   color: barColor },
    moderate: { label: 'Moderate signal', color: barColor },
    weak:     { label: 'Weak signal',     color: '#888780' },
  }[strength] || { label: strength, color: '#888780' }

  return (
    <div>
      {/* Bar track */}
      <div style={{
        height:       '10px',
        background:   'var(--color-background-secondary)',
        borderRadius: '5px',
        overflow:     'hidden',
        margin:       '8px 0 4px',
        border:       '0.5px solid var(--color-border-tertiary)',
      }}>
        <div style={{
          width:      `${confidence}%`,
          height:     '100%',
          background: barColor,
          borderRadius: '5px',
          transition: 'width 1s ease-out',
        }} />
      </div>

      {/* Labels */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        fontSize:       '11px',
        color:          'var(--color-text-secondary)',
      }}>
        <span style={{ color: strengthLabel.color, fontWeight: '500' }}>
          {strengthLabel.label}
        </span>
        <span>{confidence}% confidence</span>
      </div>
    </div>
  )
}
