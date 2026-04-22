// src/components/ui/WindowSelector.jsx

export default function WindowSelector({
  rsiWindow,
  emaWindow,
  onRsiChange,
  onEmaChange,
}) {
  const labelStyle = {
    fontSize: '11px',
    color:    'var(--color-text-secondary)',
    display:  'flex',
    alignItems: 'center',
    gap:      '6px',
  }

  const inputStyle = {
    width:        '56px',
    fontSize:     '12px',
    padding:      '3px 6px',
    border:       '0.5px solid var(--color-border-tertiary)',
    borderRadius: 'var(--border-radius-md)',
    background:   'var(--color-background-secondary)',
    color:        'var(--color-text-primary)',
    textAlign:    'center',
  }

  return (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
      <label style={labelStyle}>
        RSI window
        <input
          type="number"
          min="2"
          max="50"
          value={rsiWindow}
          onChange={(e) => onRsiChange(Number(e.target.value))}
          style={inputStyle}
        />
      </label>

      <label style={labelStyle}>
        EMA window
        <input
          type="number"
          min="2"
          max="200"
          value={emaWindow}
          onChange={(e) => onEmaChange(Number(e.target.value))}
          style={inputStyle}
        />
      </label>
    </div>
  )
}
