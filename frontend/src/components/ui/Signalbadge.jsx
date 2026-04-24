// src/components/ui/SignalBadge.jsx

// Maps indicator readings to human-friendly labels and colours
const RSI_SIGNALS = {
  overbought: { label: 'RSI — Overbought', color: '#E24B4A', bg: '#FCEBEB', tip: 'RSI above 70. Price may be due for a pullback.' },
  oversold: { label: 'RSI — Oversold', color: '#1D9E75', bg: '#E1F5EE', tip: 'RSI below 30. Price may be due for a bounce.' },
  neutral: { label: 'RSI — Neutral', color: '#888780', bg: '#F1EFE8', tip: 'RSI between 30–70. No extreme reading.' },
}

const EMA_SIGNALS = {
  above: { label: 'EMA — Price above trend', color: '#1D9E75', bg: '#E1F5EE', tip: 'Price is above EMA. Uptrend in place.' },
  below: { label: 'EMA — Price below trend', color: '#E24B4A', bg: '#FCEBEB', tip: 'Price is below EMA. Downtrend in place.' },
}

const MACD_SIGNALS = {
  bullish: { label: 'MACD — Bullish crossover', color: '#1D9E75', bg: '#E1F5EE', tip: 'MACD crossed above signal line. Bullish momentum.' },
  bearish: { label: 'MACD — Bearish crossover', color: '#E24B4A', bg: '#FCEBEB', tip: 'MACD crossed below signal line. Bearish momentum.' },
  null: { label: 'MACD — No crossover', color: '#888780', bg: '#F1EFE8', tip: 'No recent MACD crossover.' },
}

export function RSIBadge({ signal }) {
  const s = RSI_SIGNALS[signal] || RSI_SIGNALS.neutral
  return <SignalPill label={s.label} color={s.color} bg={s.bg} tip={s.tip} />
}

export function EMABadge({ signal }) {
  const s = EMA_SIGNALS[signal] || EMA_SIGNALS.above
  return <SignalPill label={s.label} color={s.color} bg={s.bg} tip={s.tip} />
}

export function MACDBadge({ crossover }) {
  const key = crossover || 'null'
  const s = MACD_SIGNALS[key] || MACD_SIGNALS.null
  return <SignalPill label={s.label} color={s.color} bg={s.bg} tip={s.tip} />
}

function SignalPill({ label, color, bg, tip }) {
  return (
    <div title={tip} style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      fontSize: '11px',
      fontWeight: '500',
      padding: '4px 12px',
      borderRadius: '20px',
      background: bg,
      color,
      border: `0.5px solid ${color}44`,
      cursor: 'help',
    }}>
      {label}
    </div>
  )
}

// ── Generic action badge (buy / sell / hold) used by FII-DII components ──────

const ACTION_MAP = {
  buy: { label: 'BUY', color: '#1D9E75', bg: '#E1F5EE' },
  sell: { label: 'SELL', color: '#E24B4A', bg: '#FCEBEB' },
  hold: { label: 'HOLD', color: '#BA7517', bg: '#FDF3E3' },
  neutral: { label: 'HOLD', color: '#888780', bg: '#F1EFE8' },
}

export default function SignalBadge({ signal, size = 'md' }) {
  if (!signal) return null
  const key = signal.toLowerCase()
  const s = ACTION_MAP[key] || ACTION_MAP.neutral
  return (
    <span style={{
      display: 'inline-block',
      fontSize: size === 'sm' ? '9px' : '10px',
      fontWeight: '600',
      padding: size === 'sm' ? '1px 6px' : '2px 8px',
      borderRadius: '20px',
      background: s.bg,
      color: s.color,
      border: `0.5px solid ${s.color}44`,
      letterSpacing: '0.3px',
    }}>
      {s.label}
    </span>
  )
}
