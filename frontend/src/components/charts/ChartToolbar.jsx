// src/components/charts/ChartToolbar.jsx

const INTERVALS = [
  { label: '1D', value: '1d' },
  { label: '1W', value: '1wk' },
  { label: '1M', value: '1mo' },
]

const OVERLAYS = [
  { key: 'ema',    label: 'EMA' },
  { key: 'volume', label: 'Volume' },
  { key: 'fvg',    label: 'FVG zones' },
]

export default function ChartToolbar({
  interval,
  overlays,
  onIntervalChange,
  onOverlayToggle,
}) {
  const chipStyle = (active) => ({
    fontSize:     '11px',
    padding:      '4px 10px',
    borderRadius: '20px',
    border:       '0.5px solid var(--color-border-tertiary)',
    background:   active
      ? 'var(--color-text-primary)'
      : 'var(--color-background-secondary)',
    color:        active
      ? 'var(--color-background-primary)'
      : 'var(--color-text-secondary)',
    cursor:       'pointer',
    fontWeight:   active ? '500' : '400',
    transition:   'all 0.15s',
  })

  return (
    <div style={{
      display:     'flex',
      gap:         '6px',
      alignItems:  'center',
      marginBottom: '12px',
      flexWrap:    'wrap',
    }}>
      {/* Interval chips */}
      {INTERVALS.map(({ label, value }) => (
        <button
          key={value}
          onClick={() => onIntervalChange(value)}
          style={chipStyle(interval === value)}
        >
          {label}
        </button>
      ))}

      <div style={{
        width:      '0.5px',
        height:     '18px',
        background: 'var(--color-border-tertiary)',
        margin:     '0 4px',
      }} />

      {/* Overlay toggles */}
      {OVERLAYS.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onOverlayToggle(key)}
          style={chipStyle(overlays[key])}
        >
          {label}
        </button>
      ))}
    </div>
  )
}