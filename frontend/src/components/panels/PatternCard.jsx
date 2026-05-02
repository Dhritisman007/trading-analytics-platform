// src/components/panels/PatternCard.jsx

import { formatDate } from '../../utils/formatters'

const RELIABILITY_COLOR = {
    very_high: '#1D9E75',
    high: '#5DCAA5',
    medium: '#BA7517',
    low: '#888780',
}

const PATTERN_EMOJI = {
    bullish: '🟢',
    bearish: '🔴',
    neutral: '⚪',
}

export default function PatternCard({ patterns = [], summary = {} }) {
    return (
        <div>
            {/* Summary */}
            {summary.count > 0 && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    marginBottom: '12px',
                    padding: '10px 12px',
                    background: `${summary.color}12`,
                    border: `0.5px solid ${summary.color}30`,
                    borderRadius: 'var(--border-radius-md)',
                }}>
                    <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        background: `${summary.color}20`,
                        border: `1.5px solid ${summary.color}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '14px',
                        flexShrink: 0,
                    }}>
                        {summary.bullish_count > summary.bearish_count ? '🟢' :
                            summary.bearish_count > summary.bullish_count ? '🔴' : '⚪'}
                    </div>
                    <div>
                        <p style={{
                            fontSize: '13px',
                            fontWeight: '500',
                            color: summary.color,
                            margin: '0 0 2px',
                            textTransform: 'capitalize',
                        }}>
                            {summary.signal} pattern bias
                        </p>
                        <p style={{
                            fontSize: '11px',
                            color: 'var(--color-text-secondary)',
                            margin: 0,
                        }}>
                            {summary.bullish_count} bullish · {summary.bearish_count} bearish ·
                            {summary.reliable_count} high reliability
                        </p>
                    </div>
                </div>
            )}

            {/* Pattern list */}
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {patterns.length === 0 ? (
                    <p style={{
                        textAlign: 'center',
                        padding: '2rem',
                        color: 'var(--color-text-tertiary)',
                        fontSize: '12px',
                    }}>
                        No patterns detected in recent candles
                    </p>
                ) : (
                    patterns.map((p, i) => (
                        <div key={i} style={{
                            display: 'flex',
                            gap: '10px',
                            padding: '8px 10px',
                            borderRadius: 'var(--border-radius-md)',
                            marginBottom: '5px',
                            background: p.type === 'bullish' ? '#1D9E7508' :
                                p.type === 'bearish' ? '#E24B4A08' : 'var(--color-background-secondary)',
                            border: `0.5px solid ${p.type === 'bullish' ? '#1D9E7530' :
                                p.type === 'bearish' ? '#E24B4A30' :
                                    'var(--color-border-tertiary)'
                                }`,
                        }}>
                            {/* Emoji */}
                            <span style={{ fontSize: '16px', flexShrink: 0 }}>
                                {PATTERN_EMOJI[p.type]}
                            </span>

                            {/* Details */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                                    <span style={{
                                        fontSize: '12px',
                                        fontWeight: '500',
                                        color: p.type === 'bullish' ? '#1D9E75' :
                                            p.type === 'bearish' ? '#E24B4A' : '#888780',
                                    }}>
                                        {p.name}
                                    </span>
                                    <span style={{
                                        fontSize: '9px',
                                        padding: '1px 5px',
                                        borderRadius: '10px',
                                        background: `${RELIABILITY_COLOR[p.reliability] || '#888780'}20`,
                                        color: RELIABILITY_COLOR[p.reliability] || '#888780',
                                        fontWeight: '500',
                                    }}>
                                        {p.reliability?.replace('_', ' ')}
                                    </span>
                                    <span style={{
                                        fontSize: '9px',
                                        color: 'var(--color-text-tertiary)',
                                    }}>
                                        {p.candles}c
                                    </span>
                                </div>
                                <p style={{
                                    fontSize: '10px',
                                    color: 'var(--color-text-secondary)',
                                    margin: 0,
                                    lineHeight: '1.4',
                                    overflow: 'hidden',
                                    display: '-webkit-box',
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: 'vertical',
                                }}>
                                    {p.description}
                                </p>
                            </div>

                            {/* Date + price */}
                            <div style={{ textAlign: 'right', flexShrink: 0 }}>
                                <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 1px' }}>
                                    {formatDate(p.date)}
                                </p>
                                <p style={{ fontSize: '11px', fontWeight: '500', color: 'var(--color-text-primary)', margin: 0 }}>
                                    ₹{p.price}
                                </p>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}