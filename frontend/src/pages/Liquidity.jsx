// src/pages/Liquidity.jsx

import { useState }           from 'react'
import { useLiquidity }       from '../hooks/useLiquidity'
import VolumeProfileChart     from '../components/charts/VolumeProfileChart'
import SweepTimeline          from '../components/panels/SweepTimeline'
import VolumeAnalysisCard     from '../components/panels/VolumeAnalysisCard'
import SymbolSelector         from '../components/ui/SymbolSelector'
import { LoadingSpinner }     from '../components/ui/LoadingSpinner'
import { ErrorMessage }       from '../components/ui/ErrorMessage'
import { formatPrice }        from '../utils/formatters'

export default function Liquidity() {
  const [symbol, setSymbol] = useState('^NSEI')
  const [period, setPeriod] = useState('3mo')
  const [activeTab, setActiveTab] = useState('sweeps')

  const { data, isLoading, error, refetch } = useLiquidity(symbol, period)

  const vp      = data?.volume_profile  || {}
  const vwap    = data?.vwap            || {}
  const vol     = data?.volume_analysis || {}
  const sweeps  = data?.sweeps          || []
  const summary = data?.sweep_summary   || {}

  const tabStyle = (active) => ({
    fontSize:     '12px',
    fontWeight:   '500',
    padding:      '7px 16px',
    borderRadius: 'var(--border-radius-md)',
    border:       '0.5px solid var(--color-border-tertiary)',
    background:   active ? 'var(--color-text-primary)' : 'var(--color-background-secondary)',
    color:        active ? 'var(--color-background-primary)' : 'var(--color-text-secondary)',
    cursor:       'pointer',
    transition:   'all 0.15s',
  })

  if (isLoading) return <LoadingSpinner />
  if (error)     return <ErrorMessage message={error.message} onRetry={refetch} />

  return (
    <div>
      {/* Header */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'flex-start',
        marginBottom:   '1.25rem',
        flexWrap:       'wrap',
        gap:            '10px',
      }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 3px' }}>
            Volume & Liquidity
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
            Volume Profile · VWAP · Liquidity Sweeps · Volume Analysis
          </p>
        </div>
        <SymbolSelector
          symbol={symbol}
          period={period}
          onSymbolChange={setSymbol}
          onPeriodChange={setPeriod}
        />
      </div>

      {/* Key metrics strip */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap:                 '8px',
        marginBottom:        '1.25rem',
      }}>
        {[
          {
            label: 'Current price',
            value: formatPrice(data?.latest_price),
          },
          {
            label: 'POC',
            value: vp.poc ? `₹${vp.poc}` : '—',
            color: '#BA7517',
            hint:  'Point of Control — most traded price',
          },
          {
            label: 'VAH',
            value: vp.vah ? `₹${vp.vah}` : '—',
            color: '#378ADD',
            hint:  'Value Area High',
          },
          {
            label: 'VAL',
            value: vp.val ? `₹${vp.val}` : '—',
            color: '#7F77DD',
            hint:  'Value Area Low',
          },
          {
            label: 'VWAP',
            value: vwap.vwap ? `₹${vwap.vwap}` : '—',
            color: vwap.above_vwap ? '#1D9E75' : '#E24B4A',
            hint:  vwap.above_vwap ? 'Price above VWAP — bullish' : 'Price below VWAP — bearish',
          },
          {
            label: 'Sweeps detected',
            value: summary.total || 0,
            color: summary.bias === 'bullish' ? '#1D9E75' : summary.bias === 'bearish' ? '#E24B4A' : '#888780',
          },
          {
            label: 'Vol zone',
            value: vp.position?.replace(/_/g, ' ') || '—',
            color: vp.signal === 'bullish' ? '#1D9E75' : '#E24B4A',
          },
          {
            label: 'Vol trend',
            value: vol.vol_trend || '—',
            color: vol.vol_trend === 'expanding' ? '#1D9E75' : vol.vol_trend === 'contracting' ? '#E24B4A' : '#888780',
          },
        ].map(({ label, value, color, hint }) => (
          <div
            key={label}
            title={hint || ''}
            style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-md)',
              padding:      '10px 12px',
              cursor:       hint ? 'help' : 'default',
            }}
          >
            <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 3px' }}>
              {label}
            </p>
            <p style={{
              fontSize:      '14px',
              fontWeight:    '500',
              color:         color || 'var(--color-text-primary)',
              margin:        0,
              textTransform: 'capitalize',
            }}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Main layout — Volume Profile on left, content on right */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: '280px 1fr',
        gap:                 '12px',
        alignItems:          'start',
      }}>

        {/* Volume Profile sidebar */}
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem',
          position:     'sticky',
          top:          '1.5rem',
        }}>
          <div style={{ marginBottom: '12px' }}>
            <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 4px' }}>
              Volume Profile
            </p>
            <p style={{ fontSize: '10px', color: 'var(--color-text-secondary)', margin: 0 }}>
              {period} · {vp.histogram?.length || 0} price levels
            </p>
          </div>

          {/* Legend */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginBottom: '10px' }}>
            {[
              { color: '#BA7517', label: 'POC — most traded' },
              { color: '#378ADD', label: 'VAH — value area top' },
              { color: '#7F77DD', label: 'VAL — value area bottom' },
              { color: '#378ADD40', label: 'Value Area (70% vol)' },
            ].map(({ color, label }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{
                  width:        '10px',
                  height:       '10px',
                  background:   color,
                  borderRadius: '2px',
                  flexShrink:   0,
                }} />
                <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>
                  {label}
                </span>
              </div>
            ))}
          </div>

          <VolumeProfileChart
            histogram={vp.histogram || []}
            poc={vp.poc}
            vah={vp.vah}
            val={vp.val}
            currentPrice={data?.latest_price}
            height={600}
          />

          {/* Signal */}
          {vp.signal_desc && (
            <div style={{
              marginTop:    '10px',
              padding:      '8px 10px',
              background:   vp.signal === 'bullish' ? '#E1F5EE' : '#FCEBEB',
              borderRadius: 'var(--border-radius-md)',
              fontSize:     '11px',
              color:        vp.signal === 'bullish' ? '#085041' : '#791F1F',
              lineHeight:   '1.5',
            }}>
              {vp.signal_desc}
            </div>
          )}
        </div>

        {/* Right panel — tabs */}
        <div>
          {/* Tab bar */}
          <div style={{
            display:      'flex',
            gap:          '6px',
            marginBottom: '12px',
          }}>
            {[
              { key: 'sweeps', label: `Sweeps (${sweeps.length})` },
              { key: 'volume', label: 'Volume Analysis' },
              { key: 'vwap',   label: 'VWAP Levels' },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                style={tabStyle(activeTab === key)}
              >
                {label}
              </button>
            ))}
          </div>

          {/* ── Sweeps tab ──────────────────────────────────────────── */}
          {activeTab === 'sweeps' && (
            <div>
              {/* Sweep summary */}
              <div style={{
                display:             'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap:                 '8px',
                marginBottom:        '12px',
              }}>
                {[
                  { label: 'Total sweeps',  value: summary.total,       color: 'var(--color-text-primary)' },
                  { label: 'Bullish',       value: summary.bullish,     color: '#1D9E75' },
                  { label: 'Bearish',       value: summary.bearish,     color: '#E24B4A' },
                  { label: 'High volume',   value: summary.high_volume, color: '#BA7517' },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{
                    background:   'var(--color-background-primary)',
                    border:       '0.5px solid var(--color-border-tertiary)',
                    borderRadius: 'var(--border-radius-md)',
                    padding:      '10px 12px',
                    textAlign:    'center',
                  }}>
                    <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 3px' }}>
                      {label}
                    </p>
                    <p style={{ fontSize: '20px', fontWeight: '500', color, margin: 0 }}>
                      {value ?? '—'}
                    </p>
                  </div>
                ))}
              </div>

              {/* What is a liquidity sweep */}
              <div style={{
                background:   'var(--color-background-primary)',
                border:       '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding:      '1rem 1.25rem',
                marginBottom: '12px',
              }}>
                <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 8px' }}>
                  What is a Liquidity Sweep?
                </p>
                <div style={{
                  display:             'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap:                 '8px',
                }}>
                  {[
                    {
                      color:  '#1D9E75',
                      title:  '▲ Bullish Sweep',
                      desc:   'Price wicks below a recent swing low — triggering stop losses of long traders — then rapidly reverses back up. Institutions grabbed cheap liquidity before pushing price higher.',
                    },
                    {
                      color:  '#E24B4A',
                      title:  '▼ Bearish Sweep',
                      desc:   'Price wicks above a recent swing high — triggering stop losses of short traders — then rapidly reverses back down. Institutions sold into the breakout before pushing price lower.',
                    },
                  ].map(({ color, title, desc }) => (
                    <div key={title} style={{
                      padding:      '10px 12px',
                      background:   `${color}08`,
                      borderRadius: 'var(--border-radius-md)',
                      borderLeft:   `3px solid ${color}`,
                    }}>
                      <p style={{ fontSize: '12px', fontWeight: '600', color, margin: '0 0 5px' }}>
                        {title}
                      </p>
                      <p style={{
                        fontSize:   '11px',
                        color:      'var(--color-text-secondary)',
                        margin:     0,
                        lineHeight: '1.5',
                      }}>
                        {desc}
                      </p>
                    </div>
                  ))}
                </div>
                <p style={{
                  fontSize:   '11px',
                  color:      'var(--color-text-tertiary)',
                  margin:     '8px 0 0',
                }}>
                  ⚡ High-volume sweeps are most significant — they confirm institutional participation.
                </p>
              </div>

              {/* Sweep timeline */}
              <div style={{
                background:   'var(--color-background-primary)',
                border:       '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding:      '1rem 1.25rem',
              }}>
                <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
                  Sweep Timeline — most recent first
                </p>
                <SweepTimeline sweeps={sweeps} />
              </div>
            </div>
          )}

          {/* ── Volume tab ──────────────────────────────────────────── */}
          {activeTab === 'volume' && (
            <div style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-lg)',
              padding:      '1rem 1.25rem',
            }}>
              <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
                Volume Analysis
              </p>
              <VolumeAnalysisCard
                vol={vol}
                bars={vol.recent_bars || []}
              />
            </div>
          )}

          {/* ── VWAP tab ────────────────────────────────────────────── */}
          {activeTab === 'vwap' && (
            <div style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-lg)',
              padding:      '1rem 1.25rem',
            }}>
              <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
                VWAP + Standard Deviation Bands
              </p>

              {/* VWAP levels */}
              <div style={{
                display:             'grid',
                gridTemplateColumns: '1fr 1fr',
                gap:                 '8px',
                marginBottom:        '14px',
              }}>
                {[
                  { label: 'VWAP',       value: vwap.vwap,      color: '#378ADD' },
                  { label: '+1σ Upper',  value: vwap.upper_1sd, color: '#E24B4A60' },
                  { label: '-1σ Lower',  value: vwap.lower_1sd, color: '#1D9E7560' },
                  { label: '+2σ Upper',  value: vwap.upper_2sd, color: '#E24B4A' },
                  { label: '-2σ Lower',  value: vwap.lower_2sd, color: '#1D9E75' },
                  { label: 'Std Dev',    value: vwap.std },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{
                    display:        'flex',
                    justifyContent: 'space-between',
                    padding:        '8px 10px',
                    background:     'var(--color-background-secondary)',
                    borderRadius:   'var(--border-radius-md)',
                  }}>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                      {label}
                    </span>
                    <span style={{
                      fontSize:   '12px',
                      fontWeight: '500',
                      color:      color || 'var(--color-text-primary)',
                    }}>
                      {value ? `₹${value}` : '—'}
                    </span>
                  </div>
                ))}
              </div>

              {/* Signal */}
              <div style={{
                padding:      '12px 14px',
                background:   vwap.above_vwap ? '#E1F5EE' : '#FCEBEB',
                borderRadius: 'var(--border-radius-md)',
                marginBottom: '10px',
              }}>
                <p style={{
                  fontSize:   '13px',
                  fontWeight: '500',
                  color:      vwap.above_vwap ? '#085041' : '#791F1F',
                  margin:     '0 0 4px',
                }}>
                  Price {vwap.above_vwap ? 'above' : 'below'} VWAP by {Math.abs(parseFloat(vwap.diff_pct || 0)).toFixed(2)}%
                </p>
                <p style={{
                  fontSize:   '11px',
                  color:      vwap.above_vwap ? '#085041' : '#791F1F',
                  margin:     0,
                  opacity:    0.85,
                }}>
                  {vwap.description}
                </p>
              </div>

              {/* What is VWAP */}
              <div style={{
                padding:      '10px 12px',
                background:   'var(--color-background-secondary)',
                borderRadius: 'var(--border-radius-md)',
                fontSize:     '11px',
                color:        'var(--color-text-secondary)',
                lineHeight:   '1.6',
              }}>
                <strong style={{ color: 'var(--color-text-primary)' }}>What is VWAP? </strong>
                The Volume Weighted Average Price is the benchmark institutional traders use.
                If price is above VWAP, institutions are net buyers and the market has bullish bias.
                The ±1σ bands contain ~68% of price action. Beyond ±2σ is considered extreme and
                tends to revert. Institutions often add to positions near VWAP.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
