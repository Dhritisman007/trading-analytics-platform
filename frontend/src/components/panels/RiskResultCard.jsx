// src/components/panels/RiskResultCard.jsx

import { formatPrice, formatNumber, formatPct } from '../../utils/formatters'

const Row = ({ label, value, color }) => (
  <div style={{
    display:        'flex',
    justifyContent: 'space-between',
    alignItems:     'center',
    padding:        '6px 0',
    borderBottom:   '0.5px solid var(--color-border-tertiary)',
  }}>
    <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
      {label}
    </span>
    <span style={{
      fontSize:   '13px',
      fontWeight: '500',
      color:      color || 'var(--color-text-primary)',
    }}>
      {value}
    </span>
  </div>
)

export default function RiskResultCard({ result }) {
  if (!result) return null

  const pos   = result.position_size  || {}
  const rr    = result.risk_reward    || {}
  const score = result.trade_score    || {}
  const proj  = result.projections    || {}
  const bev   = result.breakeven      || {}
  const atr   = result.atr_stops      || null

  const gradeColors = {
    A: '#1D9E75', B: '#5DCAA5',
    C: '#BA7517', D: '#E24B4A', F: '#791F1F',
  }
  const gradeColor = gradeColors[score.grade] || '#888780'

  return (
    <div>
      {/* Trade grade hero */}
      <div style={{
        display:      'flex',
        alignItems:   'center',
        gap:          '16px',
        background:   `${gradeColor}12`,
        border:       `1px solid ${gradeColor}40`,
        borderRadius: 'var(--border-radius-lg)',
        padding:      '14px 16px',
        marginBottom: '12px',
      }}>
        <div style={{
          width:        '56px',
          height:       '56px',
          borderRadius: '50%',
          background:   `${gradeColor}20`,
          border:       `2px solid ${gradeColor}`,
          display:      'flex',
          alignItems:   'center',
          justifyContent: 'center',
          fontSize:     '24px',
          fontWeight:   '500',
          color:        gradeColor,
          flexShrink:   0,
        }}>
          {score.grade || '—'}
        </div>
        <div>
          <p style={{
            fontSize:   '14px',
            fontWeight: '500',
            color:      gradeColor,
            margin:     '0 0 4px',
          }}>
            {score.recommendation || '—'}
          </p>
          <p style={{
            fontSize: '11px',
            color:    'var(--color-text-secondary)',
            margin:   0,
          }}>
            Score: {score.score}/100 · R:R {rr.rr_display}
          </p>
        </div>
      </div>

      {/* Position sizing */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '12px 14px',
        marginBottom: '10px',
      }}>
        <p style={{
          fontSize:     '12px',
          fontWeight:   '500',
          margin:       '0 0 8px',
          color:        'var(--color-text-primary)',
        }}>
          Position sizing
        </p>
        <Row label="Units to buy"    value={pos.units} />
        <Row label="Total cost"      value={formatPrice(pos.total_cost)} />
        <Row label="Capital used"    value={`${pos.capital_used_pct}%`} />
        <Row
          label="Max risk"
          value={formatPrice(pos.risk_amount)}
          color="#E24B4A"
        />
        <Row
          label="Actual risk %"
          value={`${pos.risk_pct_actual}%`}
          color="#E24B4A"
        />
        {pos.capital_warning && (
          <p style={{
            fontSize:   '10px',
            color:      '#BA7517',
            margin:     '6px 0 0',
            lineHeight: '1.4',
          }}>
            ⚠ {pos.capital_warning}
          </p>
        )}
      </div>

      {/* R:R + projections */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '12px 14px',
        marginBottom: '10px',
      }}>
        <p style={{
          fontSize:     '12px',
          fontWeight:   '500',
          margin:       '0 0 8px',
          color:        'var(--color-text-primary)',
        }}>
          Risk / Reward
        </p>
        <Row label="R:R ratio"      value={rr.rr_display} />
        <Row label="Quality"        value={rr.quality}
             color={
               rr.quality === 'EXCELLENT' ? '#1D9E75' :
               rr.quality === 'GOOD'      ? '#5DCAA5' :
               rr.quality === 'FAIR'      ? '#BA7517' : '#E24B4A'
             }
        />
        <Row
          label="Max profit"
          value={formatPrice(proj.max_profit)}
          color="#1D9E75"
        />
        <Row
          label="Max loss"
          value={formatPrice(proj.max_loss)}
          color="#E24B4A"
        />
        <Row label="Breakeven"      value={formatPrice(bev.breakeven_price)} />
        <Row label="Profit at 2R"   value={formatPrice(proj.profit_at_2r)}
             color="#1D9E75"
        />
      </div>

      {/* ATR stops */}
      {atr && (
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '12px 14px',
          marginBottom: '10px',
        }}>
          <p style={{
            fontSize:     '12px',
            fontWeight:   '500',
            margin:       '0 0 8px',
          }}>
            ATR-based levels
          </p>
          <Row label="ATR value"   value={formatPrice(atr.atr)} />
          <Row label="ATR stop"    value={formatPrice(atr.stop_loss)}   color="#E24B4A" />
          <Row label="ATR target"  value={formatPrice(atr.target_price)} color="#1D9E75" />
          <p style={{
            fontSize:   '10px',
            color:      'var(--color-text-tertiary)',
            margin:     '6px 0 0',
            lineHeight: '1.4',
          }}>
            {atr.explanation}
          </p>
        </div>
      )}

      {/* Score factors */}
      {score.factors?.length > 0 && (
        <div style={{
          background:   'var(--color-background-secondary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-md)',
          padding:      '10px 12px',
        }}>
          <p style={{
            fontSize:      '10px',
            fontWeight:    '500',
            color:         'var(--color-text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            margin:        '0 0 6px',
          }}>
            Score breakdown
          </p>
          {score.factors.map((f, i) => (
            <p key={i} style={{
              fontSize:   '11px',
              color:      'var(--color-text-secondary)',
              margin:     '3px 0',
            }}>
              · {f}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}