// src/components/panels/SMCSummaryPanel.jsx

import { formatPrice } from '../../utils/formatters'
import SignalBadge from '../ui/Signalbadge'

export default function SMCSummaryPanel({ smcData }) {
    if (!smcData) return null

    const summary = smcData.summary || {}
    const structure = smcData.market_structure || {}
    const pd = smcData.premium_discount || {}
    const obs = smcData.unmitigated_obs || []
    const sweeps = smcData.liquidity_sweeps || []

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
            gap: '8px',
            marginBottom: '10px',
        }}>
            {/* Trend */}
            <div style={{
                background: 'var(--color-background-secondary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-md)',
                padding: '10px 12px',
            }}>
                <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>
                    Market structure
                </p>
                <SignalBadge signal={summary.trend} />
            </div>

            {/* Zone */}
            <div style={{
                background: 'var(--color-background-secondary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-md)',
                padding: '10px 12px',
            }}>
                <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>
                    Price zone
                </p>
                <p style={{
                    fontSize: '13px',
                    fontWeight: '500',
                    color: pd.zone_color || 'var(--color-text-primary)',
                    margin: 0,
                    textTransform: 'capitalize',
                }}>
                    {pd.zone || '—'} ({pd.position_pct}%)
                </p>
            </div>

            {/* Unmitigated OBs */}
            <div style={{
                background: 'var(--color-background-secondary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-md)',
                padding: '10px 12px',
            }}>
                <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>
                    Unmitigated OBs
                </p>
                <p style={{ fontSize: '20px', fontWeight: '500', margin: 0 }}>
                    {obs.length}
                </p>
            </div>

            {/* Recent sweeps */}
            <div style={{
                background: 'var(--color-background-secondary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-md)',
                padding: '10px 12px',
            }}>
                <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>
                    Recent sweeps
                </p>
                <p style={{ fontSize: '20px', fontWeight: '500', margin: 0 }}>
                    {sweeps.length}
                </p>
            </div>

            {/* Latest price vs nearest OB */}
            {obs.length > 0 && (
                <div style={{
                    background: 'var(--color-background-secondary)',
                    border: '0.5px solid var(--color-border-tertiary)',
                    borderRadius: 'var(--border-radius-md)',
                    padding: '10px 12px',
                    gridColumn: 'span 2',
                }}>
                    <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>
                        Nearest unmitigated OB
                    </p>
                    <p style={{
                        fontSize: '12px',
                        fontWeight: '500',
                        color: obs[0].type === 'bullish' ? '#1D9E75' : '#E24B4A',
                        margin: 0,
                    }}>
                        {obs[0].type === 'bullish' ? '↑ Bullish' : '↓ Bearish'} OB ·
                        {formatPrice(obs[0].bottom)} – {formatPrice(obs[0].top)} ·
                        {obs[0].strength}
                    </p>
                </div>
            )}
        </div>
    )
}