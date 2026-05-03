// src/components/panels/VolumeAnalysisCard.jsx

import { formatNumber } from '../../utils/formatters'

export default function VolumeAnalysisCard({ vol = {}, bars = [] }) {
  const trendColor = vol.vol_trend === 'expanding'   ? '#1D9E75' :
                     vol.vol_trend === 'contracting' ? '#E24B4A' : '#888780'

  const maxVol = Math.max(...bars.map((b) => b.volume), 1)

  return (
    <div>
      {/* Stats */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap:                 '8px',
        marginBottom:        '14px',
      }}>
        {[
          {
            label: 'Today volume',
            value: vol.latest_volume?.toLocaleString('en-IN') || '—',
            color: vol.is_high_volume ? '#1D9E75' : 'var(--color-text-primary)',
          },
          {
            label: '20D avg',
            value: vol.avg_volume_20?.toLocaleString('en-IN') || '—',
          },
          {
            label: 'Vol ratio',
            value: `${vol.ratio_20}×`,
            color: vol.ratio_20 > 1.5 ? '#1D9E75' : vol.ratio_20 < 0.7 ? '#E24B4A' : 'inherit',
          },
          {
            label: 'Vol trend',
            value: vol.vol_trend || '—',
            color: trendColor,
          },
          {
            label: 'Up volume',
            value: `${vol.up_volume_pct}%`,
            color: '#1D9E75',
          },
          {
            label: 'Down volume',
            value: `${vol.down_volume_pct}%`,
            color: '#E24B4A',
          },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background:   'var(--color-background-secondary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-md)',
            padding:      '8px 10px',
            textAlign:    'center',
          }}>
            <p style={{ fontSize: '9px', color: 'var(--color-text-tertiary)', margin: '0 0 2px' }}>
              {label}
            </p>
            <p style={{
              fontSize:      '13px',
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

      {/* Up vs Down volume bar */}
      <div style={{ marginBottom: '14px' }}>
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          fontSize:       '10px',
          color:          'var(--color-text-secondary)',
          marginBottom:   '4px',
        }}>
          <span style={{ color: '#1D9E75' }}>Up volume {vol.up_volume_pct}%</span>
          <span style={{ color: '#E24B4A' }}>Down volume {vol.down_volume_pct}%</span>
        </div>
        <div style={{
          height:       '8px',
          borderRadius: '4px',
          overflow:     'hidden',
          display:      'flex',
        }}>
          <div style={{
            width:      `${vol.up_volume_pct}%`,
            background: '#1D9E75',
            transition: 'width 0.6s',
          }} />
          <div style={{
            flex:       1,
            background: '#E24B4A',
          }} />
        </div>
      </div>

      {/* Volume bars — last 30 candles */}
      <div style={{ marginBottom: '6px' }}>
        <p style={{
          fontSize:     '10px',
          fontWeight:   '500',
          color:        'var(--color-text-secondary)',
          margin:       '0 0 8px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}>
          Recent volume (30 bars)
        </p>
        <div style={{
          display:    'flex',
          alignItems: 'flex-end',
          gap:        '2px',
          height:     '60px',
        }}>
          {bars.map((bar, i) => {
            const heightPct = (bar.volume / maxVol) * 100
            const color     = bar.is_up
              ? bar.vol_ratio > 1.5 ? '#1D9E75' : '#1D9E7560'
              : bar.vol_ratio > 1.5 ? '#E24B4A' : '#E24B4A60'

            return (
              <div
                key={i}
                title={`${bar.date}: ${bar.volume.toLocaleString()} (${bar.vol_ratio}× avg)`}
                style={{
                  flex:         1,
                  height:       `${heightPct}%`,
                  background:   color,
                  borderRadius: '1px 1px 0 0',
                  minHeight:    '2px',
                  cursor:       'default',
                }}
              />
            )
          })}
        </div>
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          fontSize:       '9px',
          color:          'var(--color-text-tertiary)',
          marginTop:      '3px',
        }}>
          <span>30 days ago</span>
          <span>Today</span>
        </div>
      </div>

      <p style={{
        fontSize:   '11px',
        color:      'var(--color-text-secondary)',
        margin:     0,
        lineHeight: '1.5',
        padding:    '8px 10px',
        background: 'var(--color-background-secondary)',
        borderRadius: 'var(--border-radius-md)',
      }}>
        {vol.description}
      </p>
    </div>
  )
}
