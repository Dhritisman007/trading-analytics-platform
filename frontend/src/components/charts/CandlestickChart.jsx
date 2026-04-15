/**
 * Component: CandlestickChart
 * OHLC candlestick chart
 */

import React from 'react';
import './CandlestickChart.css';

export function CandlestickChart({ 
  data = [],
  height = 400,
  showVolume = true,
}) {
  if (!data || data.length === 0) {
    return (
      <div className="chart chart--empty" style={{ height }}>
        <p>No data available</p>
      </div>
    );
  }

  // Find min/max for scaling
  const allPrices = data.flatMap(d => [d.open, d.high, d.low, d.close]);
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);
  const priceRange = maxPrice - minPrice;

  const chartWidth = data.length * 20;
  const chartHeight = height - (showVolume ? 100 : 0);

  const scalePrice = (price) => {
    return chartHeight - ((price - minPrice) / priceRange) * chartHeight * 0.8;
  };

  return (
    <div className="chart candlestick-chart" style={{ height }}>
      <svg width={chartWidth} height={chartHeight} className="chart__svg">
        {/* Grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const price = minPrice + priceRange * ratio;
          const y = scalePrice(price);
          return (
            <g key={`grid-${ratio}`}>
              <line x1="0" y1={y} x2={chartWidth} y2={y} stroke="#f0f0f0" />
              <text x="5" y={y - 5} fontSize="10" fill="#999">{price.toFixed(2)}</text>
            </g>
          );
        })}

        {/* Candles */}
        {data.map((candle, idx) => {
          const x = idx * 20 + 10;
          const openY = scalePrice(candle.open);
          const closeY = scalePrice(candle.close);
          const highY = scalePrice(candle.high);
          const lowY = scalePrice(candle.low);

          const color = candle.close >= candle.open ? '#22c55e' : '#ef4444';
          const bodyTop = Math.min(openY, closeY);
          const bodyHeight = Math.abs(closeY - openY) || 1;

          return (
            <g key={`candle-${idx}`}>
              {/* Wick */}
              <line x1={x} y1={highY} x2={x} y2={lowY} stroke={color} strokeWidth="1" />
              {/* Body */}
              <rect
                x={x - 6}
                y={bodyTop}
                width="12"
                height={bodyHeight}
                fill={color}
                stroke={color}
                strokeWidth="1"
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
