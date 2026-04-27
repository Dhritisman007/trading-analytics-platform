// src/pages/Indicators.jsx

import { useState, useMemo }       from 'react'
import { useIndicators }           from '../hooks/useIndicators'
import { useMarket }               from '../hooks/useMarket'

import CandlestickChart from '../components/charts/CandlestickChart'
import RSIChart         from '../components/charts/RSIChart'
import MACDChart        from '../components/charts/MACDChart'
import IndicatorCard    from '../components/panels/IndicatorCard'
import SymbolSelector   from '../components/ui/SymbolSelector'
import WindowSelector   from '../components/ui/WindowSelector'
import { RSIBadge, EMABadge, MACDBadge } from '../components/ui/SignalBadge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage }   from '../components/ui/ErrorMessage'

import { formatNumber, formatPrice } from '../utils/formatters'

// Beginner-friendly explainers shown under each indicator card
const EXPLAINERS = {
  rsi:  'RSI measures how fast price is moving. Above 70 = too fast upward (may fall). Below 30 = too fast downward (may rise).',
  ema:  'EMA is a moving average that reacts faster to recent prices. When price is above EMA, the trend is up.',
  macd: 'MACD shows momentum. When the histogram turns green, buyers are gaining strength. Red = sellers taking over.',
  atr:  'ATR measures how much the market moves on an average day. Useful for deciding stop-loss distance.',
}

export default function Indicators() {
  const [symbol,    setSymbol]    = useState('^NSEI')
  const [period,    setPeriod]    = useState('3mo')
  const [rsiWindow, setRsiWindow] = useState(14)
  const [emaWindow, setEmaWindow] = useState(20)

  const {
    data:      indData,
    isLoading: iLoading,
    error:     iError,
    refetch,
  } = useIndicators(symbol, period, rsiWindow, emaWindow)

  const {
    data:      market,
    isLoading: mLoading,
  } = useMarket(symbol, period)

  const isLoading = iLoading || mLoading

  // Latest reading from the last candle
  const latest = useMemo(() => {
    if (!indData?.data?.length) return null
    return indData.data[indData.data.length - 1]
  }, [indData])

  const signals = indData?.latest || {}
  const candles = market?.data    || []

  if (isLoading) return <LoadingSpinner />
  if (iError)    return <ErrorMessage message={iError.message} onRetry={refetch} />

  return (
    <div>

      {/* ── Page header ──────────────────────────────────────── */}
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
            Technical Indicators
          </h1>
          <p style={{
            fontSize: '12px',
            color:    'var(--color-text-secondary)',
            margin:   0,
          }}>
            {indData?.name} · {indData?.count} candles · {indData?.period}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <SymbolSelector
            symbol={symbol}
            period={period}
            onSymbolChange={setSymbol}
            onPeriodChange={setPeriod}
          />
          <WindowSelector
            rsiWindow={rsiWindow}
            emaWindow={emaWindow}
            onRsiChange={setRsiWindow}
            onEmaChange={setEmaWindow}
          />
        </div>
      </div>

      {/* ── Signal badges ─────────────────────────────────────── */}
      <div style={{
        display:      'flex',
        gap:          '6px',
        flexWrap:     'wrap',
        marginBottom: '1.25rem',
      }}>
        <RSIBadge  signal={signals.rsi_signal} />
        <EMABadge  signal={signals.price_vs_ema} />
        <MACDBadge crossover={signals.macd_crossover} />
      </div>

      {/* ── Indicator cards ───────────────────────────────────── */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
        gap:                 '8px',
        marginBottom:        '1.25rem',
      }}>
        <IndicatorCard
          label="RSI (14)"
          value={formatNumber(latest?.rsi)}
          description={signals.rsi_signal || '—'}
          color={
            signals.rsi_signal === 'overbought' ? '#E24B4A' :
            signals.rsi_signal === 'oversold'   ? '#1D9E75' :
            '#888780'
          }
          explainer={EXPLAINERS.rsi}
        />
        <IndicatorCard
          label={`EMA (${emaWindow})`}
          value={formatPrice(latest?.ema)}
          description={signals.price_vs_ema === 'above' ? 'Price above EMA' : 'Price below EMA'}
          color={signals.price_vs_ema === 'above' ? '#1D9E75' : '#E24B4A'}
          explainer={EXPLAINERS.ema}
        />
        <IndicatorCard
          label="MACD"
          value={formatNumber(latest?.macd)}
          subValue={`Signal: ${formatNumber(latest?.macd_signal)}`}
          description={
            latest?.macd_histogram >= 0
              ? 'Bullish momentum'
              : 'Bearish momentum'
          }
          color={latest?.macd_histogram >= 0 ? '#1D9E75' : '#E24B4A'}
          explainer={EXPLAINERS.macd}
        />
        <IndicatorCard
          label="ATR (14)"
          value={formatNumber(latest?.atr)}
          subValue={`${formatNumber(signals.atr_pct)}% of price`}
          description="Volatility measure"
          color="#BA7517"
          explainer={EXPLAINERS.atr}
        />
      </div>

      {/* ── Price + EMA chart ─────────────────────────────────── */}
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
          marginBottom:   '10px',
        }}>
          <p style={{
            fontSize:   '13px',
            fontWeight: '500',
            color:      'var(--color-text-primary)',
            margin:     0,
          }}>
            Price + EMA ({emaWindow}) overlay
          </p>
          <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
            <span style={{ color: '#1D9E75' }}>● Price</span>
            <span style={{ color: '#378ADD' }}>● EMA {emaWindow}</span>
          </div>
        </div>

        <CandlestickChart
          data={candles}
          emaData={indData?.data || []}
          showVolume={false}
          showEMA={true}
          showFVG={false}
          height={260}
        />
      </div>

      {/* ── RSI chart ─────────────────────────────────────────── */}
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
          marginBottom:   '10px',
        }}>
          <p style={{
            fontSize:   '13px',
            fontWeight: '500',
            color:      'var(--color-text-primary)',
            margin:     0,
          }}>
            RSI ({rsiWindow}) — Relative Strength Index
          </p>
          <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
            <span style={{ color: '#E24B4A' }}>— 70 overbought</span>
            <span style={{ color: '#1D9E75' }}>— 30 oversold</span>
          </div>
        </div>

        <RSIChart data={indData?.data || []} height={150} />

        {/* RSI reading explanation */}
        <div style={{
          marginTop:  '10px',
          padding:    '8px 12px',
          background: 'var(--color-background-secondary)',
          borderRadius: 'var(--border-radius-md)',
          fontSize:   '12px',
          color:      'var(--color-text-secondary)',
        }}>
          Current RSI: <strong style={{
            color:
              signals.rsi_signal === 'overbought' ? '#E24B4A' :
              signals.rsi_signal === 'oversold'   ? '#1D9E75' :
              'var(--color-text-primary)',
          }}>
            {formatNumber(latest?.rsi)} ({signals.rsi_signal || '—'})
          </strong>
          {' · '}
          {EXPLAINERS.rsi}
        </div>
      </div>

      {/* ── MACD chart ────────────────────────────────────────── */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '1rem 1.25rem',
      }}>
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          marginBottom:   '10px',
        }}>
          <p style={{
            fontSize:   '13px',
            fontWeight: '500',
            color:      'var(--color-text-primary)',
            margin:     0,
          }}>
            MACD — Moving Average Convergence Divergence
          </p>
          <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
            <span style={{ color: '#1D9E75' }}>■ Histogram</span>
            <span style={{ color: '#BA7517' }}>— MACD</span>
            <span style={{ color: '#E24B4A' }}>— Signal</span>
          </div>
        </div>

        <MACDChart data={indData?.data || []} height={160} />

        {/* MACD reading explanation */}
        <div style={{
          marginTop:    '10px',
          padding:      '8px 12px',
          background:   'var(--color-background-secondary)',
          borderRadius: 'var(--border-radius-md)',
          fontSize:     '12px',
          color:        'var(--color-text-secondary)',
        }}>
          Histogram: <strong style={{
            color: latest?.macd_histogram >= 0 ? '#1D9E75' : '#E24B4A',
          }}>
            {formatNumber(latest?.macd_histogram, 4)}
            {latest?.macd_histogram >= 0 ? ' (bullish)' : ' (bearish)'}
          </strong>
          {' · '}
          {EXPLAINERS.macd}
        </div>
      </div>

    </div>
  )
}