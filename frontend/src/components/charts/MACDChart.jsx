// src/components/charts/MACDChart.jsx

import { useEffect, useRef } from 'react'
import { createChart, CrosshairMode, LineSeries, HistogramSeries } from 'lightweight-charts'

export default function MACDChart({ data = [], height = 140 }) {
  const containerRef = useRef(null)
  const chartRef     = useRef(null)

  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const colors = {
    text:      isDark ? '#9c9a92' : '#5F5E5A',
    grid:      isDark ? '#2C2C2A' : '#F1EFE8',
    border:    isDark ? '#444441' : '#D3D1C7',
    crosshair: isDark ? '#888780' : '#B4B2A9',
  }

  useEffect(() => {
    if (!containerRef.current || !data.length) return

    const chart = createChart(containerRef.current, {
      width:  containerRef.current.clientWidth,
      height,
      layout: {
        background:  { color: 'transparent' },
        textColor:   colors.text,
        fontSize:    10,
        fontFamily:  '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: colors.crosshair, width: 1, style: 2 },
        horzLine: { color: colors.crosshair, width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor:  colors.border,
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor:    colors.border,
        timeVisible:    true,
        secondsVisible: false,
      },
    })

    // MACD histogram — coloured by positive/negative
    const histogramSeries = chart.addSeries(HistogramSeries, {
      priceLineVisible: false,
      lastValueVisible: false,
    })

    // MACD line
    const macdSeries = chart.addSeries(LineSeries, {
      color:            '#BA7517',
      lineWidth:        1.5,
      priceLineVisible: false,
      lastValueVisible: true,
    })

    // Signal line
    const signalSeries = chart.addSeries(LineSeries, {
      color:            '#E24B4A',
      lineWidth:        1.5,
      priceLineVisible: false,
      lastValueVisible: true,
    })

    const histData = data
      .filter((d) => d.macd_histogram != null)
      .map((d) => ({
        time:  d.date,
        value: d.macd_histogram,
        color: d.macd_histogram >= 0 ? '#1D9E7580' : '#E24B4A80',
      }))

    const macdData = data
      .filter((d) => d.macd != null)
      .map((d) => ({ time: d.date, value: d.macd }))

    const signalData = data
      .filter((d) => d.macd_signal != null)
      .map((d) => ({ time: d.date, value: d.macd_signal }))

    histogramSeries.setData(histData)
    macdSeries.setData(macdData)
    signalSeries.setData(signalData)

    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, height])

  if (!data.length) return (
    <div style={{
      height,
      display:        'flex',
      alignItems:     'center',
      justifyContent: 'center',
      color:          'var(--color-text-tertiary)',
      fontSize:       '12px',
    }}>
      No MACD data
    </div>
  )

  return <div ref={containerRef} style={{ width: '100%', height }} />
}
