// src/pages/Dashboard.jsx

import { useState, useCallback } from 'react'
import { useMarket }             from '../hooks/useMarket'
import { useIndicators, useLatestSignals } from '../hooks/useIndicators'
import { useFiiDiiToday }        from '../hooks/useFiiDii'
import { useMarketMood }         from '../hooks/useNews'

import CandlestickChart  from '../components/charts/CandlestickChart'
import ChartToolbar      from '../components/charts/ChartToolbar'
import CrosshairTooltip  from '../components/charts/CrosshairTooltip'
import LivePriceTicker   from '../components/panels/LivePriceTicker'
import SymbolSelector    from '../components/ui/SymbolSelector'
import { StatCard }      from '../components/ui/StatCard'
import { Badge }         from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage }  from '../components/ui/ErrorMessage'

import {
  formatPrice, formatPct, formatCrore,
  getSentimentColor, getSignalColor,
} from '../utils/formatters'

export default function Dashboard() {
  const [symbol,   setSymbol]   = useState('^NSEI')
  const [period,   setPeriod]   = useState('3mo')
  const [interval, setInterval] = useState('1d')
  const [overlays, setOverlays] = useState({
    ema:    true,
    volume: true,
    fvg:    false,
  })
  const [hoveredCandle, setHoveredCandle] = useState(null)

  // Data hooks
  const { data: market,     isLoading: mLoading, error: mError, refetch } =
    useMarket(symbol, period)
  const { data: indicators, isLoading: iLoading } =
    useIndicators(symbol, period)
  const { data: signals } =
    useLatestSignals(symbol)
  const { data: fiiToday } =
    useFiiDiiToday()
  const { data: mood } =
    useMarketMood()

  const handleOverlayToggle = useCallback((key) => {
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  const isLoading = mLoading || iLoading

  if (isLoading) return <LoadingSpinner />
  if (mError)    return <ErrorMessage message={mError.message} onRetry={refetch} />

  const summary  = market?.summary    || {}
  const latest   = signals?.latest    || {}
  const candles  = market?.data       || []
  const indData  = indicators?.data   || []
  const fii      = fiiToday?.fii      || {}
  const dii      = fiiToday?.dii      || {}
  const signal   = fiiToday?.signal   || {}

  return (
    <div>
      {/* ── Page header ─────────────────────────────────────────── */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'flex-start',
        marginBottom:   '1.25rem',
        flexWrap:       'wrap',
        gap:            '10px',
      }}>
        <div>
          <h1 style={{
            fontSize:   '20px',
            fontWeight: '500',
            margin:     '0 0 3px',
            color:      'var(--color-text-primary)',
          }}>
            {market?.name || 'Market Dashboard'}
          </h1>
          <p style={{
            fontSize: '12px',
            color:    'var(--color-text-secondary)',
            margin:   0,
          }}>
            {market?.count} candles · {market?.period} ·{' '}
            <span style={{ color: market?._cache === 'HIT' ? '#1D9E75' : '#BA7517' }}>
              {market?._cache === 'HIT' ? 'cached' : 'live'}
            </span>
          </p>
        </div>
        <SymbolSelector
          symbol={symbol}
          period={period}
          onSymbolChange={setSymbol}
          onPeriodChange={setPeriod}
        />
      </div>

      {/* ── Stat cards ───────────────────────────────────────────── */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap:                 '8px',
        marginBottom:        '1.25rem',
      }}>
        <StatCard
          label="Last close"
          value={formatPrice(summary.latest_close)}
          change={summary.change_pct}
        />
        <StatCard
          label="Change"
          value={formatPct(summary.change_pct)}
          color={summary.change_pct >= 0 ? '#1D9E75' : '#E24B4A'}
        />
        <StatCard
          label="Period high"
          value={formatPrice(summary.period_high)}
          color="#1D9E75"
        />
        <StatCard
          label="Period low"
          value={formatPrice(summary.period_low)}
          color="#E24B4A"
        />
        <StatCard
          label="RSI (14)"
          value={latest.rsi_value || '—'}
          color={
            latest.rsi_signal === 'overbought' ? '#E24B4A' :
            latest.rsi_signal === 'oversold'   ? '#1D9E75' :
            'var(--color-text-primary)'
          }
        />
        <StatCard
          label="EMA position"
          value={latest.price_vs_ema || '—'}
          color={latest.price_vs_ema === 'above' ? '#1D9E75' : '#E24B4A'}
        />
      </div>

      {/* ── Main chart card ──────────────────────────────────────── */}
      <div style={{
        background:    'var(--color-background-primary)',
        border:        '0.5px solid var(--color-border-tertiary)',
        borderRadius:  'var(--border-radius-lg)',
        padding:       '1rem 1.25rem',
        marginBottom:  '10px',
      }}>
        <ChartToolbar
          interval={interval}
          overlays={overlays}
          onIntervalChange={setInterval}
          onOverlayToggle={handleOverlayToggle}
        />

        <CandlestickChart
          data={candles}
          emaData={indData}
          showVolume={overlays.volume}
          showEMA={overlays.ema}
          showFVG={overlays.fvg}
          height={380}
          onCrosshair={setHoveredCandle}
        />

        <CrosshairTooltip data={hoveredCandle} />
      </div>

      {/* ── Live ticker ──────────────────────────────────────────── */}
      <LivePriceTicker
        symbol={symbol}
        lastClose={summary.latest_close}
      />

      {/* ── Bottom row — FII/DII + News mood ────────────────────── */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: '1fr 1fr',
        gap:                 '10px',
        marginTop:           '10px',
      }}>

        {/* FII/DII today */}
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem 1.25rem',
        }}>
          <p style={{
            fontSize:     '13px',
            fontWeight:   '500',
            margin:       '0 0 12px',
            color:        'var(--color-text-primary)',
          }}>
            Institutional flows today
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {[
              { label: 'FII net', value: fii.net, action: fii.action },
              { label: 'DII net', value: dii.net, action: dii.action },
            ].map(({ label, value, action }) => (
              <div key={label} style={{
                display:        'flex',
                justifyContent: 'space-between',
                alignItems:     'center',
              }}>
                <span style={{
                  fontSize: '12px',
                  color:    'var(--color-text-secondary)',
                }}>
                  {label}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{
                    fontSize:   '13px',
                    fontWeight: '500',
                    color:      action === 'buy' ? '#1D9E75' : '#E24B4A',
                  }}>
                    {value != null ? formatCrore(value) : '—'}
                  </span>
                  <Badge
                    label={action || '—'}
                    color={action === 'buy' ? '#1D9E75' : '#E24B4A'}
                  />
                </div>
              </div>
            ))}

            {signal.signal && (
              <div style={{
                marginTop:    '8px',
                paddingTop:   '8px',
                borderTop:    '0.5px solid var(--color-border-tertiary)',
                fontSize:     '11px',
                color:        signal.color || 'var(--color-text-secondary)',
                fontWeight:   '500',
              }}>
                {signal.signal}
              </div>
            )}
          </div>
        </div>

        {/* News mood */}
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem 1.25rem',
        }}>
          <p style={{
            fontSize:     '13px',
            fontWeight:   '500',
            margin:       '0 0 12px',
            color:        'var(--color-text-primary)',
          }}>
            Market sentiment
          </p>

          {mood?.market_mood ? (
            <div>
              <div style={{
                display:     'flex',
                alignItems:  'center',
                gap:         '10px',
                marginBottom: '10px',
              }}>
                <span style={{
                  fontSize:   '20px',
                  fontWeight: '500',
                  color:      mood.market_mood.overall_color,
                }}>
                  {mood.market_mood.overall_label?.toUpperCase()}
                </span>
                <span style={{
                  fontSize: '12px',
                  color:    'var(--color-text-secondary)',
                }}>
                  {mood.market_mood.total} articles analysed
                </span>
              </div>

              {/* Sentiment bar */}
              <div style={{
                display:      'flex',
                height:       '6px',
                borderRadius: '3px',
                overflow:     'hidden',
                gap:          '2px',
              }}>
                {[
                  { pct: mood.market_mood.sentiment_distribution?.positive_pct, color: '#1D9E75' },
                  { pct: mood.market_mood.sentiment_distribution?.neutral_pct,  color: '#888780' },
                  { pct: mood.market_mood.sentiment_distribution?.negative_pct, color: '#E24B4A' },
                ].map(({ pct, color }, i) => (
                  <div key={i} style={{
                    width:      `${pct || 0}%`,
                    background: color,
                  }} />
                ))}
              </div>

              <div style={{
                display:  'flex',
                gap:      '12px',
                marginTop: '6px',
              }}>
                {[
                  { label: 'Positive', count: mood.market_mood.positive_count, color: '#1D9E75' },
                  { label: 'Neutral',  count: mood.market_mood.neutral_count,  color: '#888780' },
                  { label: 'Negative', count: mood.market_mood.negative_count, color: '#E24B4A' },
                ].map(({ label, count, color }) => (
                  <span key={label} style={{ fontSize: '11px', color }}>
                    {label}: {count}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
              Loading sentiment data...
            </p>
          )}
        </div>

      </div>
    </div>
  )
}