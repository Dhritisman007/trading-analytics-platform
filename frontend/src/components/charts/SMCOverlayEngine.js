// src/components/charts/SMCOverlayEngine.js
// lightweight-charts v5 API — uses chart.addSeries(LineSeries, opts)

import { LineSeries } from 'lightweight-charts'

export function drawOrderBlocks(chart, orderBlocks = [], latestDate) {
  const series = []
  orderBlocks.forEach((ob) => {
    if (!ob.date || !ob.top || !ob.bottom) return
    const isBull      = ob.type === 'bullish'
    const isMitigated = ob.mitigated
    const baseColor   = isBull ? '#1D9E75' : '#E24B4A'
    const border      = `${baseColor}${isMitigated ? '40' : '80'}`
    const endDate     = latestDate || ob.date
    try {
      const topLine = chart.addSeries(LineSeries, {
        color: border, lineWidth: 1, lineStyle: isMitigated ? 3 : 0,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      const bottomLine = chart.addSeries(LineSeries, {
        color: border, lineWidth: 1, lineStyle: isMitigated ? 3 : 0,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      topLine.setData([
        { time: ob.date, value: parseFloat(ob.top) },
        { time: endDate, value: parseFloat(ob.top) },
      ])
      bottomLine.setData([
        { time: ob.date, value: parseFloat(ob.bottom) },
        { time: endDate, value: parseFloat(ob.bottom) },
      ])
      topLine.setMarkers([{
        time:     ob.date,
        position: isBull ? 'belowBar' : 'aboveBar',
        color:    baseColor,
        shape:    'square',
        text:     `${isBull ? '▲' : '▼'} OB${isMitigated ? ' ✓' : ''}`,
        size:     0,
      }])
      series.push(topLine, bottomLine)
    } catch (e) { /* skip invalid dates */ }
  })
  return series
}

export function drawLiquiditySweeps(chart, sweeps = []) {
  const allSeries = []
  sweeps.forEach((sweep) => {
    if (!sweep.date) return
    const isBull = sweep.type === 'bullish'
    const color  = isBull ? '#1D9E75' : '#E24B4A'
    const level  = parseFloat(sweep.swept_level || 0)
    if (!level) return
    try {
      const s = chart.addSeries(LineSeries, {
        color: `${color}60`, lineWidth: 1, lineStyle: 2,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      s.setData([{ time: sweep.date, value: level }])
      s.setMarkers([{
        time:     sweep.date,
        position: isBull ? 'belowBar' : 'aboveBar',
        color,
        shape:    isBull ? 'arrowUp' : 'arrowDown',
        text:     `Sweep ${isBull ? '↑' : '↓'}`,
        size:     1,
      }])
      allSeries.push(s)
    } catch (e) { /* skip */ }
  })
  return allSeries
}

export function drawMarketStructure(chart, bos = [], choch = []) {
  const allSeries = []

  bos.forEach((event) => {
    if (!event.date || !event.broken_level) return
    const isBull = event.direction === 'bullish'
    const color  = isBull ? '#1D9E75' : '#E24B4A'
    try {
      const s = chart.addSeries(LineSeries, {
        color: `${color}50`, lineWidth: 1,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      s.setData([{ time: event.date, value: parseFloat(event.broken_level) }])
      s.setMarkers([{
        time:     event.date,
        position: isBull ? 'aboveBar' : 'belowBar',
        color,
        shape:    'square',
        text:     `BOS ${isBull ? '↑' : '↓'}`,
        size:     0,
      }])
      allSeries.push(s)
    } catch (e) { /* skip */ }
  })

  choch.forEach((event) => {
    if (!event.date || !event.broken_level) return
    try {
      const s = chart.addSeries(LineSeries, {
        color: '#7F77DD50', lineWidth: 1, lineStyle: 2,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      s.setData([{ time: event.date, value: parseFloat(event.broken_level) }])
      s.setMarkers([{
        time:     event.date,
        position: event.direction === 'bullish' ? 'aboveBar' : 'belowBar',
        color:    '#7F77DD',
        shape:    'circle',
        text:     'CHoCH',
        size:     0,
      }])
      allSeries.push(s)
    } catch (e) { /* skip */ }
  })

  return allSeries
}

export function drawEqualHighsLows(chart, equalHighs = [], equalLows = []) {
  const allSeries = []

  equalHighs.forEach((eqh) => {
    if (!eqh.level || !eqh.date_1 || !eqh.date_2) return
    try {
      const s = chart.addSeries(LineSeries, {
        color: '#E24B4A60', lineWidth: 1, lineStyle: 1,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      const level = parseFloat(eqh.level)
      s.setData([{ time: eqh.date_1, value: level }, { time: eqh.date_2, value: level }])
      s.setMarkers([{ time: eqh.date_2, position: 'aboveBar', color: '#E24B4A', shape: 'square', text: 'EQH', size: 0 }])
      allSeries.push(s)
    } catch (e) { /* skip */ }
  })

  equalLows.forEach((eql) => {
    if (!eql.level || !eql.date_1 || !eql.date_2) return
    try {
      const s = chart.addSeries(LineSeries, {
        color: '#1D9E7560', lineWidth: 1, lineStyle: 1,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      })
      const level = parseFloat(eql.level)
      s.setData([{ time: eql.date_1, value: level }, { time: eql.date_2, value: level }])
      s.setMarkers([{ time: eql.date_2, position: 'belowBar', color: '#1D9E75', shape: 'square', text: 'EQL', size: 0 }])
      allSeries.push(s)
    } catch (e) { /* skip */ }
  })

  return allSeries
}

export function drawPremiumDiscount(chart, premDisc = {}, candles = []) {
  if (!premDisc.fib_levels || !candles.length) return []
  const firstDate = candles[0]?.date
  const lastDate  = candles[candles.length - 1]?.date
  if (!firstDate || !lastDate) return []

  const allSeries  = []
  const fibConfigs = [
    { key: '0.0',   color: '#E24B4A', style: 0 },
    { key: '0.236', color: '#E24B4A', style: 2 },
    { key: '0.382', color: '#BA7517', style: 2 },
    { key: '0.5',   color: '#888780', style: 0 },
    { key: '0.618', color: '#1D9E75', style: 2 },
    { key: '0.786', color: '#1D9E75', style: 2 },
    { key: '1.0',   color: '#1D9E75', style: 0 },
  ]

  fibConfigs.forEach(({ key, color, style }) => {
    const level = parseFloat(premDisc.fib_levels[key])
    if (!level) return
    try {
      const s = chart.addSeries(LineSeries, {
        color:            `${color}50`,
        lineWidth:        key === '0.5' ? 1.5 : 1,
        lineStyle:        style,
        priceLineVisible: false,
        lastValueVisible: key === '0.5',
        crosshairMarkerVisible: false,
        title:            key === '0.5' ? 'EQ' : '',
      })
      s.setData([{ time: firstDate, value: level }, { time: lastDate, value: level }])
      allSeries.push(s)
    } catch (e) { /* skip */ }
  })

  return allSeries
}

export function drawSwingPoints(chart, swingHighs = [], swingLows = []) {
  const allSeries = []
  try {
    const validHighs = swingHighs.filter((sh) => sh.date && sh.price)
    if (validHighs.length) {
      const s = chart.addSeries(LineSeries, {
        color: 'transparent', priceLineVisible: false,
        lastValueVisible: false, crosshairMarkerVisible: false,
      })
      s.setData(validHighs.map((sh) => ({ time: sh.date, value: parseFloat(sh.price) })))
      s.setMarkers(validHighs.map((sh) => ({
        time: sh.date, position: 'aboveBar',
        color: '#E24B4A80', shape: 'circle', text: '', size: 0,
      })))
      allSeries.push(s)
    }

    const validLows = swingLows.filter((sl) => sl.date && sl.price)
    if (validLows.length) {
      const s = chart.addSeries(LineSeries, {
        color: 'transparent', priceLineVisible: false,
        lastValueVisible: false, crosshairMarkerVisible: false,
      })
      s.setData(validLows.map((sl) => ({ time: sl.date, value: parseFloat(sl.price) })))
      s.setMarkers(validLows.map((sl) => ({
        time: sl.date, position: 'belowBar',
        color: '#1D9E7580', shape: 'circle', text: '', size: 0,
      })))
      allSeries.push(s)
    }
  } catch (e) { /* skip */ }
  return allSeries
}

export function removeAllOverlaySeries(chart, seriesArray) {
  seriesArray.forEach((s) => {
    try { chart.removeSeries(s) } catch (e) { /* already removed */ }
  })
}