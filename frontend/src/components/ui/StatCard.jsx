// src/components/ui/StatCard.jsx
import { formatPct } from '../../utils/formatters'

export const StatCard = ({
  label,
  value,
  change = null,
  unit = '',
  color = 'var(--color-text-primary)',
}) => (
  <div style={{
    background:   'var(--color-background-secondary)',
    borderRadius: 'var(--border-radius-md)',
    padding:      '12px 14px',
    border:       '0.5px solid var(--color-border-tertiary)',
  }}>
    <p style={{
      fontSize: '11px',
      color:    'var(--color-text-secondary)',
      margin:   '0 0 4px',
    }}>
      {label}
    </p>
    <p style={{
      fontSize:   '22px',
      fontWeight: '500',
      color,
      margin:     '0',
    }}>
      {value}{unit}
    </p>
    {change != null && (
      <p style={{
        fontSize: '11px',
        color:    change >= 0 ? '#1D9E75' : '#E24B4A',
        margin:   '3px 0 0',
      }}>
        {formatPct(change)}
      </p>
    )}
  </div>
)