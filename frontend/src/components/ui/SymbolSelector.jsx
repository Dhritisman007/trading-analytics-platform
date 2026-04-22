// src/components/ui/SymbolSelector.jsx

import { SYMBOLS, PERIODS } from '../../utils/constants'

export default function SymbolSelector({
  symbol,
  period,
  onSymbolChange,
  onPeriodChange,
}) {
  const selectStyle = {
    fontSize:     '12px',
    padding:      '5px 10px',
    border:       '0.5px solid var(--color-border-tertiary)',
    borderRadius: 'var(--border-radius-md)',
    background:   'var(--color-background-secondary)',
    color:        'var(--color-text-primary)',
    cursor:       'pointer',
    outline:      'none',
  }

  return (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <select
        value={symbol}
        onChange={(e) => onSymbolChange(e.target.value)}
        style={selectStyle}
      >
        {SYMBOLS.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>

      <select
        value={period}
        onChange={(e) => onPeriodChange(e.target.value)}
        style={selectStyle}
      >
        {PERIODS.map((p) => (
          <option key={p.value} value={p.value}>{p.label}</option>
        ))}
      </select>
    </div>
  )
}