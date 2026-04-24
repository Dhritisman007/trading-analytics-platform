// src/components/ui/MarketMoodBadge.jsx

export default function MarketMoodBadge({ mood, size = 'md' }) {
  if (!mood) return null

  const {
    overall_label,
    overall_color,
    overall_score,
    positive_count,
    negative_count,
    neutral_count,
    total,
    sentiment_distribution: dist,
  } = mood

  const isLarge = size === 'lg'

  return (
    <div style={{
      display:     'inline-flex',
      alignItems:  'center',
      gap:         '10px',
      background:  `${overall_color}12`,
      border:      `0.5px solid ${overall_color}40`,
      borderRadius: 'var(--border-radius-lg)',
      padding:     isLarge ? '10px 16px' : '6px 12px',
    }}>
      {/* Mood label */}
      <span style={{
        fontSize:   isLarge ? '16px' : '13px',
        fontWeight: '500',
        color:      overall_color,
        textTransform: 'capitalize',
      }}>
        {overall_label}
      </span>

      {/* Score */}
      <span style={{
        fontSize: '11px',
        color:    overall_color,
        opacity:  0.8,
      }}>
        {parseFloat(overall_score) > 0 ? '+' : ''}{overall_score}
      </span>

      {/* Mini distribution bar */}
      {dist && (
        <div style={{
          display:      'flex',
          height:       '4px',
          width:        isLarge ? '80px' : '50px',
          borderRadius: '2px',
          overflow:     'hidden',
          gap:          '1px',
        }}>
          <div style={{
            width:      `${dist.positive_pct}%`,
            background: '#1D9E75',
          }} />
          <div style={{
            width:      `${dist.neutral_pct}%`,
            background: '#888780',
          }} />
          <div style={{
            width:      `${dist.negative_pct}%`,
            background: '#E24B4A',
          }} />
        </div>
      )}

      {total && (
        <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>
          {total} articles
        </span>
      )}
    </div>
  )
}