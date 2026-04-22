// src/components/panels/LivePriceTicker.jsx

import { useWebSocket } from '../../hooks/useWebSocket'
import { formatPrice, formatPct, getPriceColor } from '../../utils/formatters'

// Maps your symbol (^NSEI) to Upstox instrument key
const SYMBOL_TO_KEY = {
  '^NSEI':    'NSE_INDEX|Nifty 50',
  '^BSESN':   'BSE_INDEX|SENSEX',
  '^NSEBANK': 'NSE_INDEX|Nifty Bank',
}

export default function LivePriceTicker({ symbol = '^NSEI', lastClose = null }) {
  const { getLivePrice, connected } = useWebSocket()
  const instrumentKey = SYMBOL_TO_KEY[symbol]
  const tick          = getLivePrice(instrumentKey)

  const ltp       = tick?.ltp    ?? lastClose
  const changePct = tick?.change_pct ?? null
  const isLive    = connected && tick != null

  return (
    <div style={{
      display:        'flex',
      alignItems:     'center',
      justifyContent: 'space-between',
      background:     'var(--color-background-primary)',
      border:         '0.5px solid var(--color-border-tertiary)',
      borderRadius:   'var(--border-radius-lg)',
      padding:        '10px 16px',
    }}>
      {/* Live indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{
          width:        '7px',
          height:       '7px',
          borderRadius: '50%',
          background:   isLive ? '#1D9E75' : '#888780',
          display:      'inline-block',
          animation:    isLive ? 'pulse 2s infinite' : 'none',
        }} />
        <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}`}</style>
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          {isLive ? `Live · ${instrumentKey}` : 'Last close · WebSocket offline'}
        </span>
      </div>

      {/* Price */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{
          fontSize:   '22px',
          fontWeight: '500',
          color:      'var(--color-text-primary)',
        }}>
          {ltp ? formatPrice(ltp) : '—'}
        </span>

        {changePct != null && (
          <span style={{
            fontSize:     '12px',
            fontWeight:   '500',
            padding:      '3px 10px',
            borderRadius: '20px',
            background:   changePct >= 0 ? '#E1F5EE' : '#FCEBEB',
            color:        changePct >= 0 ? '#085041' : '#791F1F',
          }}>
            {formatPct(changePct)} today
          </span>
        )}
      </div>
    </div>
  )
}