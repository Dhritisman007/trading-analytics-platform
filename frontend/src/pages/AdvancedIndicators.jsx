// src/pages/AdvancedIndicators.jsx

import { useState } from 'react'
import { useAdvancedIndicators } from '../hooks/useAdvancedIndicators'
import BollingerChart from '../components/charts/BollingerChart'
import StochRSIChart from '../components/charts/StochRSIChart'
import AdvancedSignalRow from '../components/ui/AdvancedSignalRow'
import SymbolSelector from '../components/ui/SymbolSelector'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { formatPrice, formatNumber } from '../utils/formatters'

export default function AdvancedIndicators() {
    const [symbol, setSymbol] = useState('^NSEI')
    const [period, setPeriod] = useState('3mo')

    const { data, isLoading, error, refetch } = useAdvancedIndicators(symbol, period)

    if (isLoading) return <LoadingSpinner />
    if (error) return <ErrorMessage message={error.message} onRetry={refetch} />

    const signals = data?.signals || {}
    const overall = data?.overall_bias || {}
    const candles = data?.data || []

    return (
        <div>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '1.25rem',
                flexWrap: 'wrap',
                gap: '10px',
            }}>
                <div>
                    <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 3px' }}>
                        Advanced Indicators
                    </h1>
                    <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
                        VWAP · Supertrend · Bollinger Bands · StochRSI · Ichimoku
                    </p>
                </div>
                <SymbolSelector
                    symbol={symbol}
                    period={period}
                    onSymbolChange={setSymbol}
                    onPeriodChange={setPeriod}
                />
            </div>

            {/* Overall bias card */}
            {overall.label && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    background: `${overall.color}10`,
                    border: `1px solid ${overall.color}30`,
                    borderRadius: 'var(--border-radius-lg)',
                    padding: '12px 16px',
                    marginBottom: '12px',
                }}>
                    {/* Score circle */}
                    <div style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '50%',
                        border: `2px solid ${overall.color}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '18px',
                        fontWeight: '500',
                        color: overall.color,
                        flexShrink: 0,
                    }}>
                        {overall.score}
                    </div>
                    <div>
                        <p style={{
                            fontSize: '15px',
                            fontWeight: '500',
                            color: overall.color,
                            margin: '0 0 3px',
                        }}>
                            {overall.label}
                        </p>
                        <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', margin: 0 }}>
                            {overall.bullish} of {overall.total} advanced indicators bullish
                        </p>
                    </div>
                </div>
            )}

            {/* Signal summary */}
            <div style={{
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '1rem 1.25rem',
                marginBottom: '10px',
            }}>
                <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 10px' }}>
                    Signal summary
                </p>

                <AdvancedSignalRow
                    label="VWAP"
                    signal={signals.vwap}
                    value={signals.vwap?.vwap ? `₹${signals.vwap.vwap}` : null}
                />
                <AdvancedSignalRow
                    label="Supertrend"
                    signal={signals.supertrend}
                    value={signals.supertrend?.value ? `₹${signals.supertrend.value}` : null}
                />
                <AdvancedSignalRow
                    label="Bollinger"
                    signal={signals.bollinger}
                    value={signals.bollinger?.pct_b ? `%B: ${signals.bollinger.pct_b}` : null}
                />
                <AdvancedSignalRow
                    label="StochRSI"
                    signal={signals.stoch_rsi}
                    value={signals.stoch_rsi?.k ? `K:${signals.stoch_rsi.k} D:${signals.stoch_rsi.d}` : null}
                />
                <AdvancedSignalRow
                    label="Ichimoku"
                    signal={signals.ichimoku}
                    value={signals.ichimoku?.position?.replace('_', ' ')}
                />
            </div>

            {/* Bollinger Bands chart */}
            <div style={{
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '1rem 1.25rem',
                marginBottom: '10px',
            }}>
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                }}>
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: 0 }}>
                        Bollinger Bands (20, 2σ)
                    </p>
                    <div style={{ display: 'flex', gap: '10px', fontSize: '11px' }}>
                        {[
                            { label: 'Price', color: '#1D9E75' },
                            { label: 'Upper', color: '#E24B4A' },
                            { label: 'Middle', color: '#888780' },
                            { label: 'Lower', color: '#1D9E75' },
                        ].map(({ label, color }) => (
                            <span key={label} style={{
                                display: 'flex', alignItems: 'center', gap: '4px',
                                color: 'var(--color-text-secondary)',
                            }}>
                                <span style={{
                                    width: '12px', height: '2px',
                                    background: color, display: 'inline-block',
                                }} />
                                {label}
                            </span>
                        ))}
                    </div>
                </div>
                <BollingerChart data={candles} height={240} />

                {/* Squeeze alert */}
                {signals.bollinger?.is_squeeze && (
                    <div style={{
                        marginTop: '8px',
                        padding: '8px 12px',
                        background: '#FAEEDA',
                        borderRadius: 'var(--border-radius-md)',
                        fontSize: '12px',
                        color: '#633806',
                        fontWeight: '500',
                    }}>
                        ⚡ Bollinger Squeeze detected — bands are narrowing.
                        Big price move expected soon — direction unclear.
                    </div>
                )}

                {/* Beginner explanation */}
                <div style={{
                    marginTop: '8px',
                    padding: '10px 12px',
                    background: 'var(--color-background-secondary)',
                    borderRadius: 'var(--border-radius-md)',
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    lineHeight: '1.6',
                }}>
                    <strong style={{ color: 'var(--color-text-primary)' }}>What this means: </strong>
                    {signals.bollinger?.description}
                </div>
            </div>

            {/* Stochastic RSI chart */}
            <div style={{
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '1rem 1.25rem',
                marginBottom: '10px',
            }}>
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                }}>
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: 0 }}>
                        Stochastic RSI
                    </p>
                    <div style={{ display: 'flex', gap: '10px', fontSize: '11px' }}>
                        {[
                            { label: '%K', color: '#7F77DD' },
                            { label: '%D', color: '#BA7517' },
                        ].map(({ label, color }) => (
                            <span key={label} style={{
                                display: 'flex', alignItems: 'center', gap: '4px',
                                color: 'var(--color-text-secondary)',
                            }}>
                                <span style={{
                                    width: '12px', height: '2px',
                                    background: color, display: 'inline-block',
                                }} />
                                {label}
                            </span>
                        ))}
                    </div>
                </div>
                <StochRSIChart data={candles} height={130} />
                <div style={{
                    marginTop: '8px',
                    padding: '10px 12px',
                    background: 'var(--color-background-secondary)',
                    borderRadius: 'var(--border-radius-md)',
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    lineHeight: '1.6',
                }}>
                    <strong style={{ color: 'var(--color-text-primary)' }}>What this means: </strong>
                    {signals.stoch_rsi?.description}
                </div>
            </div>

            {/* Supertrend + VWAP details */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
            }}>
                {/* Supertrend */}
                <div style={{
                    background: 'var(--color-background-primary)',
                    border: '0.5px solid var(--color-border-tertiary)',
                    borderRadius: 'var(--border-radius-lg)',
                    padding: '1rem 1.25rem',
                }}>
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 10px' }}>
                        Supertrend (10, 3.0)
                    </p>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        marginBottom: '10px',
                    }}>
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: '50%',
                            background: `${signals.supertrend?.color || '#888780'}15`,
                            border: `2px solid ${signals.supertrend?.color || '#888780'}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '13px',
                            fontWeight: '500',
                            color: signals.supertrend?.color,
                            flexShrink: 0,
                        }}>
                            {signals.supertrend?.signal || '—'}
                        </div>
                        <div>
                            <p style={{
                                fontSize: '13px',
                                fontWeight: '500',
                                color: signals.supertrend?.color,
                                margin: '0 0 2px',
                            }}>
                                {signals.supertrend?.just_flipped
                                    ? '🔔 Signal flipped!'
                                    : 'Trend confirmed'}
                            </p>
                            <p style={{
                                fontSize: '11px',
                                color: 'var(--color-text-tertiary)',
                                margin: 0,
                            }}>
                                Level: ₹{signals.supertrend?.value}
                            </p>
                        </div>
                    </div>
                    <p style={{
                        fontSize: '11px',
                        color: 'var(--color-text-secondary)',
                        margin: 0,
                        lineHeight: '1.5',
                        padding: '8px',
                        background: 'var(--color-background-secondary)',
                        borderRadius: 'var(--border-radius-md)',
                    }}>
                        {signals.supertrend?.description}
                    </p>
                </div>

                {/* VWAP */}
                <div style={{
                    background: 'var(--color-background-primary)',
                    border: '0.5px solid var(--color-border-tertiary)',
                    borderRadius: 'var(--border-radius-lg)',
                    padding: '1rem 1.25rem',
                }}>
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 10px' }}>
                        VWAP + Bands
                    </p>
                    {[
                        { label: 'VWAP', value: signals.vwap?.vwap, color: '#378ADD' },
                        { label: '+1σ', value: candles[candles.length - 1]?.vwap_u1 },
                        { label: '-1σ', value: candles[candles.length - 1]?.vwap_l1 },
                        { label: '+2σ', value: candles[candles.length - 1]?.vwap_u2 },
                        { label: '-2σ', value: candles[candles.length - 1]?.vwap_l2 },
                    ].map(({ label, value, color }) => (
                        <div key={label} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            padding: '5px 0',
                            borderBottom: '0.5px solid var(--color-border-tertiary)',
                            fontSize: '12px',
                        }}>
                            <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
                            <span style={{
                                color: color || 'var(--color-text-primary)',
                                fontWeight: '500',
                            }}>
                                {value ? `₹${value}` : '—'}
                            </span>
                        </div>
                    ))}
                    <p style={{
                        fontSize: '11px',
                        color: 'var(--color-text-secondary)',
                        margin: '8px 0 0',
                        lineHeight: '1.5',
                    }}>
                        {signals.vwap?.description}
                    </p>
                </div>
            </div>

            {/* Ichimoku */}
            <div style={{
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-lg)',
                padding: '1rem 1.25rem',
                marginTop: '10px',
            }}>
                <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 10px' }}>
                    Ichimoku Cloud
                </p>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                    gap: '8px',
                    marginBottom: '10px',
                }}>
                    {[
                        { label: 'Tenkan (9)', value: signals.ichimoku?.tenkan },
                        { label: 'Kijun (26)', value: signals.ichimoku?.kijun },
                        { label: 'Senkou A', value: signals.ichimoku?.senkou_a },
                        { label: 'Senkou B', value: signals.ichimoku?.senkou_b },
                        { label: 'Cloud top', value: signals.ichimoku?.cloud_top },
                        { label: 'Cloud bottom', value: signals.ichimoku?.cloud_bottom },
                    ].map(({ label, value }) => (
                        <div key={label} style={{
                            background: 'var(--color-background-secondary)',
                            border: '0.5px solid var(--color-border-tertiary)',
                            borderRadius: 'var(--border-radius-md)',
                            padding: '8px 10px',
                        }}>
                            <p style={{
                                fontSize: '10px',
                                color: 'var(--color-text-tertiary)',
                                margin: '0 0 2px',
                            }}>
                                {label}
                            </p>
                            <p style={{
                                fontSize: '13px',
                                fontWeight: '500',
                                color: 'var(--color-text-primary)',
                                margin: 0,
                            }}>
                                {value ? `₹${value}` : '—'}
                            </p>
                        </div>
                    ))}
                </div>

                {/* Cloud position badge */}
                <div style={{
                    padding: '8px 12px',
                    background: `${signals.ichimoku?.color || '#888780'}15`,
                    borderRadius: 'var(--border-radius-md)',
                    fontSize: '12px',
                    color: signals.ichimoku?.color,
                    fontWeight: '500',
                    marginBottom: '8px',
                }}>
                    {signals.ichimoku?.position?.replace(/_/g, ' ').toUpperCase()} ·
                    Cloud is {signals.ichimoku?.cloud_color === '#1D9E75' ? '🟢 green (bullish)' : '🔴 red (bearish)'}
                </div>

                <p style={{
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    margin: 0,
                    lineHeight: '1.6',
                    padding: '8px 10px',
                    background: 'var(--color-background-secondary)',
                    borderRadius: 'var(--border-radius-md)',
                }}>
                    {signals.ichimoku?.description}
                </p>
            </div>
        </div>
    )
}