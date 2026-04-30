// src/components/charts/CandlestickChart.jsx

import { useEffect, useRef } from 'react'
import { createChart, ColorType, CrosshairMode, CandlestickSeries, LineSeries, HistogramSeries } from 'lightweight-charts'
import { CHART_COLORS } from '../../utils/constants'
import { cleanChartData } from '../../utils/formatters'

/**
 * Convert a date value to lightweight-charts compatible time.
 * - Daily data:   "YYYY-MM-DD" string   → kept as string
 * - Intraday:     unix seconds integer   → passed through directly
 * - Legacy:       "YYYY-MM-DD HH:MM:SS" → converted to unix seconds
 */
function toChartTime(dateVal) {
  if (dateVal === null || dateVal === undefined) return null
  // Integer unix timestamp from backend (intraday)
  if (typeof dateVal === 'number') return dateVal
  // Daily ISO date string
  if (!dateVal.includes(' ') && !dateVal.includes('T')) return dateVal
  // Legacy datetime string fallback
  return Math.floor(new Date(dateVal).getTime() / 1000)
}

/** Format a unix-second timestamp as IST time string */
const IST_TIME_FMT = new Intl.DateTimeFormat('en-IN', {
  timeZone:  'Asia/Kolkata',
  hour:      '2-digit',
  minute:    '2-digit',
  hour12:    false,
})

const IST_DATETIME_FMT = new Intl.DateTimeFormat('en-IN', {
  timeZone:  'Asia/Kolkata',
  day:       '2-digit',
  month:     'short',
  hour:      '2-digit',
  minute:    '2-digit',
  hour12:    false,
})

export default function CandlestickChart({
  data         = [],
  emaData      = [],
  fvgZones     = [],
  height       = 380,
  showVolume   = true,
  showEMA      = true,
  showFVG      = true,
  isIntraday   = false,
  onCrosshair  = null,
}) {
  const containerRef = useRef(null)
  const chartRef     = useRef(null)
  const candleRef    = useRef(null)
  const emaRef       = useRef(null)
  const volumeRef    = useRef(null)

  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  const colors = {
    background: 'transparent',
    text:       isDark ? '#9c9a92' : '#5F5E5A',
    grid:       isDark ? '#2C2C2A' : '#F1EFE8',
    border:     isDark ? '#444441' : '#D3D1C7',
    crosshair:  isDark ? '#888780' : '#B4B2A9',
  }

  useEffect(() => {
    if (!containerRef.current || !data.length) return

    const chart = createChart(containerRef.current, {
      width:  containerRef.current.clientWidth,
      height: showVolume ? height : height - 80,
      layout: {
        background:  { type: ColorType.Solid, color: colors.background },
        textColor:   colors.text,
        fontSize:    11,
        fontFamily:  '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: colors.grid, style: 1 },
        horzLines: { color: colors.grid, style: 1 },
      },
      crosshair: {
        mode:     CrosshairMode.Normal,
        vertLine: { color: colors.crosshair, width: 1, style: 2 },
        horzLine: { color: colors.crosshair, width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor:  colors.border,
        scaleMargins: { top: 0.05, bottom: showVolume ? 0.25 : 0.05 },
      },
      timeScale: {
        borderColor:    colors.border,
        timeVisible:    true,
        secondsVisible: false,
        tickMarkFormatter: isIntraday
          ? (time) => IST_TIME_FMT.format(new Date(time * 1000))
          : undefined,
      },
      localization: isIntraday ? {
        timeFormatter: (time) => IST_DATETIME_FMT.format(new Date(time * 1000)),
      } : {},
    })

    // ── Candlestick series ─────────────────────────────────────────────
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor:         CHART_COLORS.bullish,
      downColor:       CHART_COLORS.bearish,
      borderUpColor:   CHART_COLORS.bullish,
      borderDownColor: CHART_COLORS.bearish,
      wickUpColor:     CHART_COLORS.bullish,
      wickDownColor:   CHART_COLORS.bearish,
    })

    const candleData = data
      .map((d) => ({
        time:  toChartTime(d.date),
        open:  d.open,
        high:  d.high,
        low:   d.low,
        close: d.close,
      }))
      .filter((d) => d.time !== null)
      // Deduplicate by time
      .filter((d, i, arr) => i === 0 || d.time !== arr[i - 1].time)
      .sort((a, b) => (a.time > b.time ? 1 : -1))

    candleSeries.setData(candleData)
    candleRef.current = candleSeries

    // ── EMA line overlay ───────────────────────────────────────────────
    if (showEMA && emaData.length) {
      const emaSeries = chart.addSeries(LineSeries, {
        color:            CHART_COLORS.ema,
        lineWidth:        1.5,
        priceLineVisible: false,
        lastValueVisible: true,
      })
      const emaFormatted = emaData
        .filter((d) => d.ema != null)
        .map((d) => ({ time: toChartTime(d.date), value: d.ema }))
        .filter((d) => d.time !== null)
        .filter((d, i, arr) => i === 0 || d.time !== arr[i - 1].time)
        .sort((a, b) => (a.time > b.time ? 1 : -1))

      emaSeries.setData(emaFormatted)
      emaRef.current = emaSeries
    }

    // ── Volume bars ────────────────────────────────────────────────────
    if (showVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        color:        '#B4B2A9',
        priceFormat:  { type: 'volume' },
        priceScaleId: 'volume',
      })
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      })

      const volumeData = data
        .map((d) => ({
          time:  toChartTime(d.date),
          value: d.volume,
          color: d.close >= d.open
            ? `${CHART_COLORS.bullish}80`
            : `${CHART_COLORS.bearish}80`,
        }))
        .filter((d) => d.time !== null)
        .filter((d, i, arr) => i === 0 || d.time !== arr[i - 1].time)
        .sort((a, b) => (a.time > b.time ? 1 : -1))

      volumeSeries.setData(volumeData)
      volumeRef.current = volumeSeries
    }

    // ── FVG zones (daily only — skip for intraday) ─────────────────────
    if (!isIntraday && showFVG && fvgZones.length) {
      fvgZones.slice(0, 10).forEach((fvg) => {
        if (fvg.filled) return

        const color     = fvg.type === 'bullish'
          ? `${CHART_COLORS.bullish}30`
          : `${CHART_COLORS.bearish}30`
        const startDate = fvg.candle_3
        const endDate   = data[data.length - 1].date
        if (startDate === endDate) return

        const topLine = chart.addSeries(LineSeries, {
          color, lineWidth: 1, lineStyle: 2,
          priceLineVisible: false, lastValueVisible: false,
        })
        const bottomLine = chart.addSeries(LineSeries, {
          color, lineWidth: 1, lineStyle: 2,
          priceLineVisible: false, lastValueVisible: false,
        })

        topLine.setData([
          { time: startDate, value: fvg.gap_top },
          { time: endDate,   value: fvg.gap_top },
        ])
        bottomLine.setData([
          { time: startDate, value: fvg.gap_bottom },
          { time: endDate,   value: fvg.gap_bottom },
        ])
      })
    }

    // ── Crosshair subscription ─────────────────────────────────────────
    if (onCrosshair) {
      chart.subscribeCrosshairMove((param) => {
        if (param.time && candleRef.current) {
          const price = param.seriesData.get(candleRef.current)
          if (price) onCrosshair(price)
        }
      })
    }

    // ── Responsive resize ──────────────────────────────────────────────
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)
    chart.timeScale().fitContent()
    chartRef.current = chart

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, emaData, fvgZones, showVolume, showEMA, showFVG, isIntraday])

  if (!data.length) {
    return (
      <div style={{
        height,
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'center',
        color:          'var(--color-text-tertiary)',
        fontSize:       '13px',
      }}>
        No chart data available
      </div>
    )
  }

  return <div ref={containerRef} style={{ width: '100%', height }} />
}