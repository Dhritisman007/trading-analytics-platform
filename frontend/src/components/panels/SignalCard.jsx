// src/components/panels/SignalCard.jsx

import ConfidenceBar from '../ui/ConfidenceBar'
import { formatPrice } from '../../utils/formatters'

export default function SignalCard({ prediction }) {
  if (!prediction) return null

  const {
    signal,
    confidence,
    strength,
    color,
    market_context: ctx = {},
    model_info:     info = {},
    explanation:    expl = {},
  } = prediction

  const isBuy   = signal === 'BUY'
  const bgColor = isBuy ? '#E1F5EE' : '#FCEBEB'
  const txColor = isBuy ? '#085041' : '#791F1F'

  return (
    <div style={{
      background:   'var(--color-background-primary)',
      border:       `1px solid ${color || '#888780'}`,
      borderRadius: 'var(--border-radius-lg)',
      padding:      '1.25rem',
      marginBottom: '10px',
    }}>
      {/* Signal hero */}
      <div style={{
        display:     'flex',
        alignItems:  'center',
        gap:         '16px',
        marginBottom: '16px',
      }}>
        {/* Big signal badge */}
        <div style={{
          background:   bgColor,
          borderRadius: 'var(--border-radius-lg)',
          padding:      '14px 24px',
          textAlign:    'center',
          minWidth:     '90px',
        }}>
          <p style={{
            fontSize:   '28px',
            fontWeight: '500',
            color:      txColor,
            margin:     0,
          }}>
            {signal}
          </p>
          <p style={{
            fontSize: '10px',
            color:    txColor,
            margin:   '2px 0 0',
            opacity:  0.8,
          }}>
            {strength}
          </p>
        </div>

        {/* Context */}
        <div style={{ flex: 1 }}>
          <p style={{
            fontSize:     '13px',
            color:        'var(--color-text-primary)',
            margin:       '0 0 6px',
            lineHeight:   '1.5',
          }}>
            {expl.one_line || '—'}
          </p>
          <ConfidenceBar
            confidence={confidence}
            signal={signal}
            strength={strength}
          />
        </div>
      </div>

      {/* Market context pills */}
      <div style={{
        display:  'flex',
        gap:      '8px',
        flexWrap: 'wrap',
        borderTop: '0.5px solid var(--color-border-tertiary)',
        paddingTop: '12px',
      }}>
        {[
          {
            label: 'Last close',
            value: formatPrice(ctx.latest_close),
          },
          {
            label: 'RSI',
            value: ctx.rsi,
            color: ctx.rsi_signal === 'overbought' ? '#E24B4A'
                 : ctx.rsi_signal === 'oversold'   ? '#1D9E75'
                 : 'var(--color-text-primary)',
          },
          {
            label: 'EMA position',
            value: ctx.price_vs_ema,
            color: ctx.price_vs_ema === 'above' ? '#1D9E75' : '#E24B4A',
          },
          {
            label: 'Volatility',
            value: ctx.atr_pct ? `${ctx.atr_pct}%` : '—',
          },
          ...(ctx.macd_crossover ? [{
            label: 'MACD',
            value: `${ctx.macd_crossover} crossover`,
            color: ctx.macd_crossover === 'bullish' ? '#1D9E75' : '#E24B4A',
          }] : []),
        ].map(({ label, value, color: c }) => (
          <div key={label} style={{
            background:   'var(--color-background-secondary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-md)',
            padding:      '5px 10px',
          }}>
            <p style={{
              fontSize: '10px',
              color:    'var(--color-text-tertiary)',
              margin:   '0 0 1px',
            }}>
              {label}
            </p>
            <p style={{
              fontSize:   '12px',
              fontWeight: '500',
              color:      c || 'var(--color-text-primary)',
              margin:     0,
            }}>
              {value ?? '—'}
            </p>
          </div>
        ))}
      </div>

      {/* Model info footer */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        marginTop:      '10px',
        paddingTop:     '10px',
        borderTop:      '0.5px solid var(--color-border-tertiary)',
        fontSize:       '10px',
        color:          'var(--color-text-tertiary)',
        flexWrap:       'wrap',
        gap:            '6px',
      }}>
        <span>Model accuracy: {info.accuracy}%</span>
        <span>Trained on {info.train_rows} candles</span>
        <span>{info.train_period}</span>
      </div>
    </div>
  )
}