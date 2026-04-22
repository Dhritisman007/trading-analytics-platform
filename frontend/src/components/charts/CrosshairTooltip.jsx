// src/components/charts/CrosshairTooltip.jsx

import { formatPrice, formatLargeNumber } from '../../utils/formatters'

export default function CrosshairTooltip({ data }) {
  if (!data) return null

  const isUp = data.close >= data.open
  const change = data.close - data.open
  const changePct = (change / data.open) * 100

  return (
    <div style={{
      display:    'flex',
      gap:        '16px',
      flexWrap:   'wrap',
      fontSize:   '11px',
      color:      'var(--color-text-secondary)',
      padding:    '6px 0 2px',
      borderTop:  '0.5px solid var(--color-border-tertiary)',
      marginTop:  '6px',
    }}>
      {[
        { label: 'O', value: formatPrice(data.open) },
        { label: 'H', value: formatPrice(data.high),  color: '#1D9E75' },
        { label: 'L', value: formatPrice(data.low),   color: '#E24B4A' },
        { label: 'C', value: formatPrice(data.close), color: isUp ? '#1D9E75' : '#E24B4A' },
        { label: 'Chg', value: `${isUp ? '+' : ''}${changePct.toFixed(2)}%`,
          color: isUp ? '#1D9E75' : '#E24B4A' },
        { label: 'Vol', value: formatLargeNumber(data.volume) },
      ].map(({ label, value, color }) => (
        <span key={label}>
          <span style={{ color: 'var(--color-text-tertiary)' }}>{label} </span>
          <span style={{ color: color || 'var(--color-text-primary)', fontWeight: '500' }}>
            {value}
          </span>
        </span>
      ))}
    </div>
  )
}