// src/components/charts/RSIChart.jsx

import { useEffect, useRef } from 'react'
import { createChart, CrosshairMode, LineSeries } from 'lightweight-charts'

export default function RSIChart({ data = [], height = 140 }) {
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
        borderColor: colors.border,
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor:    colors.border,
        timeVisible:    true,
        secondsVisible: false,
      },
    })

    // RSI line
    const rsiSeries = chart.addSeries(LineSeries, {
      color:            '#7F77DD',
      lineWidth:        2,
      priceLineVisible: false,
      lastValueVisible: true,
    })

    // Overbought line (70)
    const overboughtSeries = chart.addSeries(LineSeries, {
      color:            '#E24B4A',
      lineWidth:        1,
      lineStyle:        2, // dashed
      priceLineVisible: false,
      lastValueVisible: false,
    })

    // Oversold line (30)
    const oversoldSeries = chart.addSeries(LineSeries, {
      color:            '#1D9E75',
      lineWidth:        1,
      lineStyle:        2,
      priceLineVisible: false,
      lastValueVisible: false,
    })

    // Midline (50)
    const midSeries = chart.addSeries(LineSeries, {
      color:            colors.border,
      lineWidth:        1,
      lineStyle:        3,
      priceLineVisible: false,
      lastValueVisible: false,
    })

    const rsiData    = data.filter((d) => d.rsi != null).map((d) => ({ time: d.date, value: d.rsi }))
    const firstTime  = rsiData[0]?.time
    const lastTime   = rsiData[rsiData.length - 1]?.time

    rsiSeries.setData(rsiData)

    if (firstTime && lastTime) {
      overboughtSeries.setData([{ time: firstTime, value: 70 }, { time: lastTime, value: 70 }])
      oversoldSeries.setData([  { time: firstTime, value: 30 }, { time: lastTime, value: 30 }])
      midSeries.setData([       { time: firstTime, value: 50 }, { time: lastTime, value: 50 }])
    }

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
      No RSI data
    </div>
  )

  return <div ref={containerRef} style={{ width: '100%', height }} />
}
