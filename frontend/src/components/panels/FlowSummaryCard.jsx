// src/components/panels/FlowSummaryCard.jsx

import { formatCrore } from '../../utils/formatters'

const StreakBadge = ({ streak }) => {
  if (!streak?.days) return null
  const color = streak.action === 'buy' ? '#1D9E75' : '#E24B4A'
  return (
    <span style={{
      fontSize:     '10px',
      fontWeight:   '500',
      padding:      '2px 9px',
      borderRadius: '20px',
      background:   `${color}18`,
      color,
      border:       `0.5px solid ${color}40`,
    }}>
      {streak.days}d {streak.action} streak
      {streak.significant ? ' 🔥' : ''}
    </span>
  )
}

const FlowRow = ({ label, data }) => {
  const net = data?.net
  const isPositive = parseFloat(net) >= 0
  return (
    <div style={{
      display:        'flex',
      justifyContent: 'space-between',
      alignItems:     'center',
      padding:        '8px 0',
      borderBottom:   '0.5px solid var(--color-border-tertiary)',
    }}>
      <div>
        <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--color-text-primary)' }}>
          {label}
        </span>
        {data?.gross_buy != null && (
          <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', marginLeft: '6px' }}>
            Buy: {formatCrore(data.gross_buy)} · Sell: {formatCrore(data.gross_sell)}
          </span>
        )}
      </div>
      <span style={{
        fontSize:   '14px',
        fontWeight: '500',
        color:      net != null ? (isPositive ? '#1D9E75' : '#E24B4A') : 'var(--color-text-tertiary)',
      }}>
        {net != null ? formatCrore(net) : '—'}
      </span>
    </div>
  )
}

export default function FlowSummaryCard({ today, signal, pressure, streaks }) {
  return (
    <div style={{
      background:   'var(--color-background-primary)',
      border:       '0.5px solid var(--color-border-tertiary)',
      borderRadius: 'var(--border-radius-lg)',
      padding:      '1rem 1.25rem',
      marginBottom: '10px',
    }}>
      {/* Signal banner */}
      {signal && (
        <div style={{
          background:   `${signal.color || '#888780'}12`,
          border:       `0.5px solid ${signal.color || '#888780'}40`,
          borderRadius: 'var(--border-radius-md)',
          padding:      '10px 14px',
          marginBottom: '14px',
          display:      'flex',
          justifyContent: 'space-between',
          alignItems:   'center',
          gap:          '8px',
          flexWrap:     'wrap',
        }}>
          <div>
            <p style={{ fontSize: '14px', fontWeight: '500', color: signal.color, margin: '0 0 3px' }}>
              {signal.signal}
            </p>
            <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', margin: 0, lineHeight: '1.4' }}>
              {signal.description}
            </p>
          </div>
          {pressure != null && (
            <span style={{
              fontSize:   '13px',
              fontWeight: '600',
              color:      parseFloat(pressure?.score) >= 0 ? '#1D9E75' : '#E24B4A',
            }}>
              Pressure: {pressure.score > 0 ? '+' : ''}{pressure.score}
            </span>
          )}
        </div>
      )}

      {/* FII / DII rows */}
      <FlowRow label="FII" data={today?.fii} />
      <FlowRow label="DII" data={today?.dii} />

      {/* Combined net */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        padding:        '8px 0',
        marginBottom:   streaks ? '12px' : 0,
      }}>
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Combined net
        </span>
        <span style={{
          fontSize:   '14px',
          fontWeight: '500',
          color:      parseFloat(today?.combined_net) >= 0 ? '#1D9E75' : '#E24B4A',
        }}>
          {today?.combined_net != null ? formatCrore(today.combined_net) : '—'}
        </span>
      </div>

      {/* Streak badges */}
      {streaks && (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {streaks.fii && <StreakBadge streak={streaks.fii} />}
          {streaks.dii && <StreakBadge streak={streaks.dii} />}
        </div>
      )}
    </div>
  )
}
