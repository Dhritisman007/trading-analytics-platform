// src/components/panels/FIIDIISummaryCard.jsx

import { formatCrore, formatNumber } from '../../utils/formatters'
import SignalBadge from '../ui/SignalBadge'

const FlowRow = ({ label, data, color }) => (
  <div style={{
    display:        'flex',
    justifyContent: 'space-between',
    alignItems:     'center',
    padding:        '7px 0',
    borderBottom:   '0.5px solid var(--color-border-tertiary)',
  }}>
    <div>
      <span style={{
        fontSize:   '12px',
        fontWeight: '500',
        color:      'var(--color-text-primary)',
      }}>
        {label}
      </span>
      <span style={{
        fontSize:   '10px',
        color:      'var(--color-text-tertiary)',
        marginLeft: '6px',
      }}>
        Buy: {formatCrore(data?.gross_buy)} · Sell: {formatCrore(data?.gross_sell)}
      </span>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span style={{
        fontSize:   '13px',
        fontWeight: '500',
        color:      parseFloat(data?.net) >= 0 ? '#1D9E75' : '#E24B4A',
      }}>
        {data?.net != null ? formatCrore(data.net) : '—'}
      </span>
      <SignalBadge signal={data?.action} size="sm" />
    </div>
  </div>
)

const StreakBadge = ({ streak }) => {
  if (!streak?.days) return null
  const color = streak.action === 'buy' ? '#1D9E75' : '#E24B4A'
  return (
    <span style={{
      fontSize:     '10px',
      fontWeight:   '500',
      padding:      '2px 8px',
      borderRadius: '20px',
      background:   `${color}18`,
      color,
    }}>
      {streak.days}d {streak.action} streak
      {streak.significant ? ' 🔥' : ''}
    </span>
  )
}

export default function FIIDIISummaryCard({ data }) {
  if (!data) return null

  const {
    today,
    signal,
    pressure,
    streaks,
    moving_averages: ma,
    period_summary:  period,
  } = data

  return (
    <div>
      {/* Signal header */}
      <div style={{
        background:   `${signal?.color || '#888780'}12`,
        border:       `0.5px solid ${signal?.color || '#888780'}40`,
        borderRadius: 'var(--border-radius-lg)',
        padding:      '12px 14px',
        marginBottom: '12px',
      }}>
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          marginBottom:   '6px',
        }}>
          <span style={{
            fontSize:   '14px',
            fontWeight: '500',
            color:      signal?.color,
          }}>
            {signal?.signal}
          </span>
          <span style={{
            fontSize:     '13px',
            fontWeight:   '500',
            color:        parseFloat(pressure?.score) >= 0 ? '#1D9E75' : '#E24B4A',
          }}>
            Pressure: {pressure?.score > 0 ? '+' : ''}{pressure?.score}
          </span>
        </div>
        <p style={{
          fontSize:   '11px',
          color:      'var(--color-text-secondary)',
          margin:     0,
          lineHeight: '1.5',
        }}>
          {signal?.description}
        </p>
      </div>

      {/* Flow rows */}
      <FlowRow label="FII" data={today?.fii} />
      <FlowRow label="DII" data={today?.dii} />

      {/* Combined net */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        padding:        '8px 0',
        marginBottom:   '12px',
      }}>
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Combined net
        </span>
        <span style={{
          fontSize:   '13px',
          fontWeight: '500',
          color:      parseFloat(today?.combined_net) >= 0 ? '#1D9E75' : '#E24B4A',
        }}>
          {today?.combined_net != null ? formatCrore(today.combined_net) : '—'}
        </span>
      </div>

      {/* Streaks */}
      {streaks && (
        <div style={{
          display:      'flex',
          gap:          '6px',
          marginBottom: '12px',
          flexWrap:     'wrap',
        }}>
          {streaks.fii && <StreakBadge streak={streaks.fii} />}
          {streaks.dii && <StreakBadge streak={streaks.dii} />}
        </div>
      )}

      {/* Moving averages */}
      {ma && (
        <div style={{
          background:   'var(--color-background-secondary)',
          borderRadius: 'var(--border-radius-md)',
          padding:      '10px 12px',
          marginBottom: '12px',
        }}>
          <p style={{
            fontSize:      '10px',
            fontWeight:    '500',
            color:         'var(--color-text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            margin:        '0 0 8px',
          }}>
            Moving averages (₹ crore)
          </p>
          <div style={{
            display:             'grid',
            gridTemplateColumns: '1fr 1fr',
            gap:                 '6px',
          }}>
            {[
              { label: 'FII 5d avg',  value: ma.fii?.['5d'] },
              { label: 'FII 10d avg', value: ma.fii?.['10d'] },
              { label: 'DII 5d avg',  value: ma.dii?.['5d'] },
              { label: 'DII 10d avg', value: ma.dii?.['10d'] },
            ].map(({ label, value }) => (
              <div key={label}>
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
                  color:      value != null && value >= 0 ? '#1D9E75' : '#E24B4A',
                  margin:     0,
                }}>
                  {value != null
                    ? `${value >= 0 ? '+' : ''}${formatNumber(value)}`
                    : '—'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Period summary */}
      {period && (
        <div style={{
          display:             'grid',
          gridTemplateColumns: '1fr 1fr',
          gap:                 '6px',
        }}>
          {[
            { label: 'FII buy days',  value: period.fii_buy_days,  color: '#1D9E75' },
            { label: 'FII sell days', value: period.fii_sell_days, color: '#E24B4A' },
            { label: 'DII buy days',  value: period.dii_buy_days,  color: '#378ADD' },
            { label: 'DII sell days', value: period.dii_sell_days, color: '#E24B4A' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              background:   'var(--color-background-secondary)',
              borderRadius: 'var(--border-radius-md)',
              padding:      '7px 10px',
            }}>
              <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 2px' }}>
                {label}
              </p>
              <p style={{ fontSize: '16px', fontWeight: '500', color, margin: 0 }}>
                {value}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}