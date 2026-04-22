// src/components/panels/IndicatorCard.jsx

export default function IndicatorCard({
  label,
  value,
  description,
  color = 'var(--color-text-primary)',
  subValue = null,
  explainer = null,
}) {
  return (
    <div style={{
      background:   'var(--color-background-secondary)',
      border:       '0.5px solid var(--color-border-tertiary)',
      borderRadius: 'var(--border-radius-md)',
      padding:      '12px 14px',
    }}>
      <p style={{
        fontSize: '11px',
        color:    'var(--color-text-secondary)',
        margin:   '0 0 4px',
      }}>
        {label}
      </p>

      <p style={{
        fontSize:   '20px',
        fontWeight: '500',
        color,
        margin:     '0 0 2px',
      }}>
        {value}
      </p>

      {subValue && (
        <p style={{
          fontSize: '11px',
          color:    'var(--color-text-secondary)',
          margin:   '0 0 4px',
        }}>
          {subValue}
        </p>
      )}

      <p style={{
        fontSize: '11px',
        color:    color,
        margin:   '0',
        opacity:  0.8,
      }}>
        {description}
      </p>

      {/* Beginner tooltip */}
      {explainer && (
        <p style={{
          fontSize:    '10px',
          color:       'var(--color-text-tertiary)',
          margin:      '6px 0 0',
          paddingTop:  '6px',
          borderTop:   '0.5px solid var(--color-border-tertiary)',
          lineHeight:  '1.5',
        }}>
          {explainer}
        </p>
      )}
    </div>
  )
}
