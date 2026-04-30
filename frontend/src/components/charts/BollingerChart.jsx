// src/components/charts/BollingerChart.jsx

import { useEffect, useRef } from 'react'
import { createChart, CrosshairMode, ColorType, LineSeries } from 'lightweight-charts'
import { cleanChartData } from '../../utils/formatters'

export default function BollingerChart({ data = [], height = 260 }) {
    const containerRef = useRef(null)

    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const textColor = isDark ? '#9c9a92' : '#5F5E5A'
    const gridColor = isDark ? '#2C2C2A' : '#F1EFE8'
    const borderColor = isDark ? '#444441' : '#D3D1C7'

    useEffect(() => {
        if (!containerRef.current || !data.length) return

        const chart = createChart(containerRef.current, {
            width:  containerRef.current.clientWidth,
            height,
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor,
                fontSize: 10,
            },
            grid: {
                vertLines: { color: gridColor },
                horzLines: { color: gridColor },
            },
            crosshair: { mode: CrosshairMode.Normal },
            rightPriceScale: { borderColor },
            timeScale: { borderColor, timeVisible: true },
        })

        // Price line
        const priceSeries = chart.addSeries(LineSeries, {
            color:            '#1D9E75',
            lineWidth:        1.5,
            priceLineVisible: false,
            lastValueVisible: true,
        })

        // Upper Bollinger Band
        const upperSeries = chart.addSeries(LineSeries, {
            color:            '#E24B4A',
            lineWidth:        1,
            lineStyle:        2,   // dashed
            priceLineVisible: false,
            lastValueVisible: false,
        })

        // Middle band (SMA)
        const middleSeries = chart.addSeries(LineSeries, {
            color:            '#888780',
            lineWidth:        1,
            lineStyle:        2,
            priceLineVisible: false,
            lastValueVisible: false,
        })

        // Lower Bollinger Band
        const lowerSeries = chart.addSeries(LineSeries, {
            color:            '#378ADD',
            lineWidth:        1,
            lineStyle:        2,
            priceLineVisible: false,
            lastValueVisible: false,
        })

        const validData = data.filter(
            (d) => d.close && d.bb_upper && d.bb_lower
        )

        priceSeries.setData(
            cleanChartData(validData.map((d) => ({ time: d.date, value: d.close })))
        )
        upperSeries.setData(
            cleanChartData(validData.map((d) => ({ time: d.date, value: d.bb_upper })))
        )
        middleSeries.setData(
            cleanChartData(validData.map((d) => ({ time: d.date, value: d.bb_middle })))
        )
        lowerSeries.setData(
            cleanChartData(validData.map((d) => ({ time: d.date, value: d.bb_lower })))
        )

        chart.timeScale().fitContent()

        const handleResize = () => {
            if (containerRef.current)
                chart.applyOptions({ width: containerRef.current.clientWidth })
        }
        window.addEventListener('resize', handleResize)

        return () => {
            window.removeEventListener('resize', handleResize)
            chart.remove()
        }
    }, [data, height])

    if (!data.length) return null
    return <div ref={containerRef} style={{ width: '100%' }} />
}
