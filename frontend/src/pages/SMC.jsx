// src/pages/SMC.jsx

import { useState }     from 'react'
import { useMarket }    from '../hooks/useMarket'
import { useLatestSignals } from '../hooks/useIndicators'

import CandlestickChart  from '../components/charts/CandlestickChart'
import FVGPanel          from '../components/panels/FVGPanel'
import SymbolSelector    from '../components/ui/SymbolSelector'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage }   from '../components/ui/ErrorMessage'
import { useQuery }      from '@tanstack/react-query'
import { fvgApi }        from '../api/endpoints'

export default function SMC() {
  const [symbol, setSymbol] = useState('^NSEI')
  const [period, setPeriod] = useState('3mo')

  const {
    data: market,
    isLoading,
    error,
    refetch,
  } = useMarket(symbol, period)

  const { data: signals }   = useLatestSignals(symbol)
  const { data: fvgData }   = useQuery({
    queryKey: ['fvg', symbol, period, false],
    queryFn:  () => fvgApi.getAll(symbol, period, false),
    staleTime: 30 * 60 * 1000,
  })

  if (isLoading) return <LoadingSpinner />
  if (error)     return <ErrorMessage message={error.message} onRetry={refetch} />

  const candles     = market?.data     || []
  const latestPrice = market?.summary?.latest_close
  const openFvgs    = fvgData?.fvgs?.filter((f) => !f.filled) || []

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
            Smart Money Concepts
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
            Fair Value Gaps · {openFvgs.length} open zones detected
          </p>
        </div>
        <SymbolSelector
          symbol={symbol}
          period={period}
          onSymbolChange={setSymbol}
          onPeriodChange={setPeriod}
        />
      </div>

      {/* What is FVG — beginner explainer */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '1rem 1.25rem',
        marginBottom: '10px',
      }}>
        <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 8px' }}>
          What is a Fair Value Gap?
        </p>
        <p style={{
          fontSize:   '12px',
          color:      'var(--color-text-secondary)',
          margin:     '0 0 8px',
          lineHeight: '1.6',
        }}>
          A Fair Value Gap (FVG) forms when price moves so fast that it skips
          over a range of prices without any trading happening there. That empty
          zone acts like a magnet — price often returns to "fill" it later.
          Traders use FVGs to identify potential support and resistance zones.
        </p>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          {[
            {
              color: '#1D9E75',
              label: 'Bullish FVG',
              desc:  'Gap left during a sharp move up. Price may return here for support.',
            },
            {
              color: '#E24B4A',
              label: 'Bearish FVG',
              desc:  'Gap left during a sharp move down. Price may return here as resistance.',
            },
          ].map(({ color, label, desc }) => (
            <div key={label} style={{
              flex:         1,
              minWidth:     '200px',
              padding:      '8px 10px',
              background:   `${color}10`,
              borderRadius: 'var(--border-radius-md)',
              borderLeft:   `3px solid ${color}`,
            }}>
              <p style={{
                fontSize:   '11px',
                fontWeight: '500',
                color,
                margin:     '0 0 3px',
              }}>
                {label}
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
      </div>

      {/* Chart with FVG zones */}
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
          <p style={{ fontSize: '13px', fontWeight: '500', margin: 0 }}>
            Price chart with FVG zones
          </p>
          <div style={{ display: 'flex', gap: '10px', fontSize: '11px' }}>
            {[
              { color: '#1D9E7550', label: 'Bullish FVG' },
              { color: '#E24B4A50', label: 'Bearish FVG' },
            ].map(({ color, label }) => (
              <span key={label} style={{
                display:    'flex',
                alignItems: 'center',
                gap:        '5px',
                color:      'var(--color-text-secondary)',
              }}>
                <span style={{
                  width:        '14px',
                  height:       '8px',
                  background:   color,
                  display:      'inline-block',
                  borderRadius: '2px',
                }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        <CandlestickChart
          data={candles}
          emaData={[]}
          fvgZones={fvgData?.fvgs || []}
          showVolume={false}
          showEMA={false}
          showFVG={true}
          height={340}
        />
      </div>

      {/* FVG panel */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '1rem 1.25rem',
      }}>
        <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
          Detected Fair Value Gaps
        </p>
        <FVGPanel
          symbol={symbol}
          period={period}
          latestPrice={latestPrice}
        />
      </div>
    </div>
  )
}