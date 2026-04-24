// src/pages/FiiDii.jsx

import { useState }      from 'react'
import { useFiiDii, useFiiDiiToday } from '../hooks/useFiiDii'

import FlowSummaryCard   from '../components/panels/FlowSummaryCard'
import FIIDIIChart       from '../components/charts/FIIDIIChart'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage }   from '../components/ui/ErrorMessage'
import { formatNumber }   from '../utils/formatters'

export default function FiiDii() {
  const [days, setDays] = useState(30)

  const { data: today,  isLoading: tLoading } = useFiiDiiToday()
  const { data: flows,  isLoading: fLoading, error, refetch } = useFiiDii(days)

  const isLoading = tLoading || fLoading
  if (isLoading) return <LoadingSpinner />
  if (error)     return <ErrorMessage message={error.message} onRetry={refetch} />

  const period  = flows?.period_summary  || {}
  const maFlows = flows?.moving_averages || {}

  return (
    <div>
      {/* Header */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'flex-start',
        marginBottom:   '1.25rem',
        flexWrap:       'wrap',
        gap:            '8px',
      }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 3px' }}>
            FII / DII Flows
          </h1>
          <p style={{
            fontSize: '12px',
            color:    'var(--color-text-secondary)',
            margin:   0,
          }}>
            Institutional investor activity · ₹ crore · NSE data
          </p>
        </div>

        {/* Days selector */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {[10, 20, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              style={{
                fontSize:     '11px',
                padding:      '4px 12px',
                borderRadius: '20px',
                border:       '0.5px solid var(--color-border-tertiary)',
                background:   days === d
                  ? 'var(--color-text-primary)'
                  : 'var(--color-background-secondary)',
                color: days === d
                  ? 'var(--color-background-primary)'
                  : 'var(--color-text-secondary)',
                cursor: 'pointer',
              }}
            >
              {d}D
            </button>
          ))}
        </div>
      </div>

      {/* Today's flow summary */}
      <FlowSummaryCard
        today={today?.today}
        signal={today?.signal}
        pressure={today?.pressure}
        streaks={today?.streaks}
      />

      {/* Flow chart */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '1rem 1.25rem',
        marginBottom: '10px',
      }}>
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          marginBottom:   '12px',
          flexWrap:       'wrap',
          gap:            '8px',
        }}>
          <p style={{ fontSize: '13px', fontWeight: '500', margin: 0 }}>
            {days}-day flow history
          </p>
          <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
            {[
              { label: 'FII net', color: '#1D9E75' },
              { label: 'DII net', color: '#378ADD' },
              { label: 'Combined', color: '#BA7517' },
            ].map(({ label, color }) => (
              <span key={label} style={{
                display:    'flex',
                alignItems: 'center',
                gap:        '4px',
                color:      'var(--color-text-secondary)',
              }}>
                <span style={{
                  width:      '14px',
                  height:     '2px',
                  background: color,
                  display:    'inline-block',
                }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        <FIIDIIChart chartData={flows?.chart_data} height={260} />
      </div>

      {/* Moving averages + period summary */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: '1fr 1fr',
        gap:                 '10px',
      }}>
        {/* Moving averages */}
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem 1.25rem',
        }}>
          <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 12px' }}>
            Moving averages (₹ cr)
          </p>
          {['5d', '10d', '30d'].map((window) => {
            const fiiMa = maFlows.fii?.[window]
            const diiMa = maFlows.dii?.[window]
            return (
              <div key={window} style={{
                display:        'flex',
                justifyContent: 'space-between',
                padding:        '6px 0',
                borderBottom:   '0.5px solid var(--color-border-tertiary)',
                fontSize:       '12px',
              }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  {window} avg
                </span>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <span style={{
                    color:      fiiMa >= 0 ? '#1D9E75' : '#E24B4A',
                    fontWeight: '500',
                  }}>
                    FII {fiiMa != null ? formatNumber(fiiMa) : '—'}
                  </span>
                  <span style={{
                    color:      diiMa >= 0 ? '#378ADD' : '#E24B4A',
                    fontWeight: '500',
                  }}>
                    DII {diiMa != null ? formatNumber(diiMa) : '—'}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Period summary */}
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem 1.25rem',
        }}>
          <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 12px' }}>
            {period.days}-day summary
          </p>
          {[
            { label: 'FII buy days',  value: period.fii_buy_days,  color: '#1D9E75' },
            { label: 'FII sell days', value: period.fii_sell_days, color: '#E24B4A' },
            { label: 'DII buy days',  value: period.dii_buy_days,  color: '#378ADD' },
            { label: 'DII sell days', value: period.dii_sell_days, color: '#E24B4A' },
            { label: 'FII total net', value: `₹${formatNumber(period.fii_total_net)} Cr`,
              color: parseFloat(period.fii_total_net) >= 0 ? '#1D9E75' : '#E24B4A' },
            { label: 'DII total net', value: `₹${formatNumber(period.dii_total_net)} Cr`,
              color: parseFloat(period.dii_total_net) >= 0 ? '#378ADD' : '#E24B4A' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              display:        'flex',
              justifyContent: 'space-between',
              padding:        '5px 0',
              borderBottom:   '0.5px solid var(--color-border-tertiary)',
              fontSize:       '12px',
            }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
              <span style={{ color, fontWeight: '500' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}