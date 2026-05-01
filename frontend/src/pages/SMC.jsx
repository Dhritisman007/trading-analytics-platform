// src/pages/SMC.jsx

import { useState }          from 'react'
import { useMarket }         from '../hooks/useMarket'
import { useSMCFull }        from '../hooks/useSMC'
import { useQuery }          from '@tanstack/react-query'
import { fvgApi }            from '../api/endpoints'

import SMCCandlestickChart   from '../components/charts/SMCCandlestickChart'
import SMCSummaryPanel       from '../components/panels/SMCSummaryPanel'
import KillZoneOverlay       from '../components/panels/KillZoneOverlay'
import FVGPanel              from '../components/panels/FVGPanel'
import SymbolSelector        from '../components/ui/SymbolSelector'
import { LoadingSpinner }    from '../components/ui/LoadingSpinner'
import { ErrorMessage }      from '../components/ui/ErrorMessage'

export default function SMC() {
  const [symbol, setSymbol] = useState('^NSEI')
  const [period, setPeriod] = useState('3mo')

  const {
    data:      market,
    isLoading: marketLoading,
    error:     marketError,
    refetch,
  } = useMarket(symbol, period)

  const {
    data:      smcRaw,
    isLoading: smcLoading,
    error:     smcError,
  } = useSMCFull(symbol, period)

  const { data: fvgData } = useQuery({
    queryKey:  ['fvg', symbol, period, false],
    queryFn:   () => fvgApi.getAll(symbol, period, false),
    staleTime: 30 * 60 * 1000,
  })

  if (marketLoading || smcLoading) return <LoadingSpinner />
  if (marketError)                  return <ErrorMessage message={marketError.message} onRetry={refetch} />

  const candles     = market?.data     || []
  const emaData     = []                           // EMA not needed separately — SMC chart has its own
  const fvgZones    = fvgData?.fvgs    || []
  const latestPrice = market?.summary?.latest_close

  // smcRaw comes back as { data: { ...smcPayload } } from axios
  const smcData = smcRaw?.data ?? smcRaw ?? null

  return (
    <div>
      {/* ── Header ── */}
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
            Order Blocks · Liquidity Sweeps · BOS / CHoCH · Kill Zones · Premium / Discount
          </p>
        </div>
        <SymbolSelector
          symbol={symbol}
          period={period}
          onSymbolChange={setSymbol}
          onPeriodChange={setPeriod}
        />
      </div>

      {/* ── Kill Zone banner ── */}
      <KillZoneOverlay />

      {/* ── SMC summary strip ── */}
      {smcData && (
        <SMCSummaryPanel smcData={smcData} />
      )}

      {smcError && (
        <div style={{
          padding:      '10px 14px',
          background:   '#E24B4A18',
          border:       '0.5px solid #E24B4A40',
          borderRadius: 'var(--border-radius-md)',
          fontSize:     '12px',
          color:        '#E24B4A',
          marginBottom: '10px',
        }}>
          ⚠ SMC analysis unavailable: {smcError.message}
        </div>
      )}

      {/* ── Main chart with all overlays ── */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '1rem 1.25rem',
        marginBottom: '10px',
      }}>
        <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 10px' }}>
          SMC Chart
          {smcData?.summary?.trend && (
            <span style={{
              marginLeft:   '10px',
              fontSize:     '11px',
              fontWeight:   '400',
              color:        smcData.summary.trend === 'bullish' ? '#1D9E75'
                          : smcData.summary.trend === 'bearish' ? '#E24B4A'
                          : 'var(--color-text-secondary)',
            }}>
              {smcData.summary.trend === 'bullish' ? '↑ Bullish structure'
               : smcData.summary.trend === 'bearish' ? '↓ Bearish structure'
               : '↔ Ranging'}
            </span>
          )}
        </p>

        <SMCCandlestickChart
          candles={candles}
          emaData={emaData}
          fvgZones={fvgZones}
          smcData={smcData}
          height={420}
        />
      </div>

      {/* ── FVG table ── */}
      <div style={{
        background:   'var(--color-background-primary)',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-lg)',
        padding:      '1rem 1.25rem',
      }}>
        <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
          Fair Value Gaps
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