// src/components/charts/SMCCandlestickChart.jsx

import { useEffect, useRef, useState } from 'react'
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
} from 'lightweight-charts'
import { CHART_COLORS } from '../../utils/constants'
import {
  drawOrderBlocks,
  drawLiquiditySweeps,
  drawMarketStructure,
  drawEqualHighsLows,
  drawPremiumDiscount,
  drawSwingPoints,
  removeAllOverlaySeries,
} from './SMCOverlayEngine'

const DEFAULT_OVERLAYS = {
  orderBlocks:      true,
  liquiditySweeps:  true,
  bosChoch:         true,
  equalHL:          false,
  premiumDiscount:  false,
  swingPoints:      false,
  ema:              true,
  volume:           true,
  fvg:              true,
}

export default function SMCCandlestickChart({
  candles  = [],
  emaData  = [],
  fvgZones = [],
  smcData  = null,
  height   = 420,
}) {
  const containerRef = useRef(null)
  const chartRef     = useRef(null)
  const seriesRef    = useRef({ candle: null, ema: null, volume: null, overlays: [] })

  const [overlays, setOverlays] = useState(DEFAULT_OVERLAYS)

  const isDark    = window.matchMedia('(prefers-color-scheme: dark)').matches
  const textColor = isDark ? '#9c9a92' : '#5F5E5A'
  const gridColor = isDark ? '#2C2C2A' : '#F1EFE8'
  const border    = isDark ? '#444441' : '#D3D1C7'

  const toggleOverlay = (key) =>
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }))

  // ── Create chart once ────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current || !candles.length) return

    const chart = createChart(containerRef.current, {
      width:  containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor,
        fontSize:   11,
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: {
        borderColor:  border,
        scaleMargins: { top: 0.05, bottom: 0.2 },
      },
      timeScale: {
        borderColor:    border,
        timeVisible:    true,
        secondsVisible: false,
      },
    })

    // ── Candlestick series (v5 API) ───────────────────────────────────
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor:         CHART_COLORS.bullish,
      downColor:       CHART_COLORS.bearish,
      borderUpColor:   CHART_COLORS.bullish,
      borderDownColor: CHART_COLORS.bearish,
      wickUpColor:     CHART_COLORS.bullish,
      wickDownColor:   CHART_COLORS.bearish,
    })

    const candleData = candles
      .map((d) => ({ time: d.date, open: d.open, high: d.high, low: d.low, close: d.close }))
      .filter((d) => d.time)
      .filter((d, i, arr) => i === 0 || d.time !== arr[i - 1].time)
      .sort((a, b) => (a.time > b.time ? 1 : -1))

    candleSeries.setData(candleData)

    // ── EMA line ──────────────────────────────────────────────────────
    const emaSeries = chart.addSeries(LineSeries, {
      color:            CHART_COLORS.ema,
      lineWidth:        1.5,
      priceLineVisible: false,
      lastValueVisible: true,
      visible:          overlays.ema,
    })
    if (emaData.length) {
      const emaFormatted = emaData
        .filter((d) => d.ema != null)
        .map((d) => ({ time: d.date, value: d.ema }))
        .filter((d) => d.time)
        .sort((a, b) => (a.time > b.time ? 1 : -1))
      emaSeries.setData(emaFormatted)
    }

    // ── Volume histogram ──────────────────────────────────────────────
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat:  { type: 'volume' },
      priceScaleId: 'volume',
      visible:      overlays.volume,
    })
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    })
    const volData = candles
      .map((d) => ({
        time:  d.date,
        value: d.volume,
        color: d.close >= d.open ? `${CHART_COLORS.bullish}70` : `${CHART_COLORS.bearish}70`,
      }))
      .filter((d) => d.time)
      .sort((a, b) => (a.time > b.time ? 1 : -1))
    volumeSeries.setData(volData)

    chart.timeScale().fitContent()
    chartRef.current         = chart
    seriesRef.current.candle = candleSeries
    seriesRef.current.ema    = emaSeries
    seriesRef.current.volume = volumeSeries

    const handleResize = () => {
      if (containerRef.current)
        chart.applyOptions({ width: containerRef.current.clientWidth })
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
    }
  }, [candles, emaData])


  // ── Draw / redraw SMC overlays ────────────────────────────────────────
  useEffect(() => {
    const chart = chartRef.current
    if (!chart || !smcData) return

    removeAllOverlaySeries(chart, seriesRef.current.overlays)
    seriesRef.current.overlays = []

    const latestDate = candles[candles.length - 1]?.date
    const newSeries  = []

    if (overlays.orderBlocks && smcData.order_blocks?.length)
      newSeries.push(...drawOrderBlocks(chart, smcData.order_blocks, latestDate))

    if (overlays.liquiditySweeps && smcData.liquidity_sweeps?.length)
      newSeries.push(...drawLiquiditySweeps(chart, smcData.liquidity_sweeps))

    if (overlays.bosChoch && smcData.market_structure)
      newSeries.push(...drawMarketStructure(
        chart,
        smcData.market_structure.bos   || [],
        smcData.market_structure.choch || [],
      ))

    if (overlays.equalHL && smcData.equal_highs_lows)
      newSeries.push(...drawEqualHighsLows(
        chart,
        smcData.equal_highs_lows.equal_highs || [],
        smcData.equal_highs_lows.equal_lows  || [],
      ))

    if (overlays.premiumDiscount && smcData.premium_discount)
      newSeries.push(...drawPremiumDiscount(chart, smcData.premium_discount, candles))

    if (overlays.swingPoints && smcData.market_structure)
      newSeries.push(...drawSwingPoints(
        chart,
        smcData.market_structure.swing_highs || [],
        smcData.market_structure.swing_lows  || [],
      ))

    // FVG zones
    if (overlays.fvg && fvgZones.length) {
      fvgZones.slice(0, 10).forEach((fvg) => {
        if (fvg.filled) return
        const lineColor = fvg.type === 'bullish' ? '#1D9E7570' : '#E24B4A70'
        try {
          const topLine = chart.addSeries(LineSeries, {
            color: lineColor, lineWidth: 1, lineStyle: 2,
            priceLineVisible: false, lastValueVisible: false,
          })
          const bottomLine = chart.addSeries(LineSeries, {
            color: lineColor, lineWidth: 1, lineStyle: 2,
            priceLineVisible: false, lastValueVisible: false,
          })
          topLine.setData([
            { time: fvg.candle_3, value: fvg.gap_top },
            { time: latestDate,   value: fvg.gap_top },
          ])
          bottomLine.setData([
            { time: fvg.candle_3, value: fvg.gap_bottom },
            { time: latestDate,   value: fvg.gap_bottom },
          ])
          newSeries.push(topLine, bottomLine)
        } catch (e) { /* skip */ }
      })
    }

    seriesRef.current.overlays = newSeries
  }, [smcData, fvgZones, overlays, candles])


  // ── Sync EMA / Volume visibility toggles ─────────────────────────────
  useEffect(() => {
    try {
      seriesRef.current.ema?.applyOptions({ visible: overlays.ema })
      seriesRef.current.volume?.applyOptions({ visible: overlays.volume })
    } catch (e) { /* chart may not be ready */ }
  }, [overlays.ema, overlays.volume])


  const TOGGLES = [
    { key: 'orderBlocks',     label: 'Order Blocks', color: '#1D9E75' },
    { key: 'liquiditySweeps', label: 'Sweeps',       color: '#BA7517' },
    { key: 'bosChoch',        label: 'BOS/CHoCH',    color: '#7F77DD' },
    { key: 'fvg',             label: 'FVG',          color: '#378ADD' },
    { key: 'equalHL',         label: 'EQH/EQL',      color: '#E24B4A' },
    { key: 'premiumDiscount', label: 'Fib/PD',       color: '#888780' },
    { key: 'swingPoints',     label: 'Swings',       color: '#5F5E5A' },
    { key: 'ema',             label: 'EMA',          color: '#378ADD' },
    { key: 'volume',          label: 'Volume',       color: '#B4B2A9' },
  ]

  if (!candles.length) return (
    <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-tertiary)', fontSize: '13px' }}>
      No chart data
    </div>
  )

  return (
    <div>
      {/* Toggle toolbar */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '10px' }}>
        {TOGGLES.map(({ key, label, color }) => {
          const active = overlays[key]
          return (
            <button
              key={key}
              onClick={() => toggleOverlay(key)}
              style={{
                fontSize:     '10px',
                fontWeight:   '500',
                padding:      '3px 10px',
                borderRadius: '20px',
                border:       `0.5px solid ${active ? color : 'var(--color-border-tertiary)'}`,
                background:   active ? `${color}18` : 'var(--color-background-secondary)',
                color:        active ? color : 'var(--color-text-tertiary)',
                cursor:       'pointer',
                transition:   'all 0.15s',
              }}
            >
              {label}
            </button>
          )
        })}
      </div>

      {/* Chart canvas */}
      <div ref={containerRef} style={{ width: '100%' }} />

      {/* Legend */}
      {smcData && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '8px', fontSize: '10px', color: 'var(--color-text-tertiary)' }}>
          {overlays.orderBlocks && (
            <>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '12px', height: '8px', background: '#1D9E7530', border: '1px solid #1D9E75', display: 'inline-block' }} />
                Bullish OB
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '12px', height: '8px', background: '#E24B4A30', border: '1px solid #E24B4A', display: 'inline-block' }} />
                Bearish OB
              </span>
            </>
          )}
          {overlays.bosChoch && <>
            <span style={{ color: '#1D9E75' }}>BOS ↑ = bullish break</span>
            <span style={{ color: '#7F77DD' }}>CHoCH = potential reversal</span>
          </>}
          {overlays.liquiditySweeps && <span style={{ color: '#BA7517' }}>▲▼ = liquidity sweep</span>}
        </div>
      )}
    </div>
  )
}