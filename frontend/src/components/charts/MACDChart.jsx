/**
 * Component: MACDChart
 * MACD indicator chart
 */

import React from 'react';
import './MACDChart.css';

export function MACDChart({ 
  data = [],
  height = 300,
}) {
  if (!data || data.length === 0) {
    return (
      <div className="chart chart--empty" style={{ height }}>
        <p>No MACD data available</p>
      </div>
    );
  }

  const allValues = data.flatMap(d => [d.macd, d.signal, d.histogram]);
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const valueRange = maxValue - minValue;

  const chartWidth = data.length * 10;
  const chartHeight = height - 40;
  const midline = chartHeight / 2;

  const scaleValue = (value) => {
    const normalized = (value - minValue) / valueRange;
    return midline - (normalized - 0.5) * chartHeight;
  };

  return (
    <div className="chart macd-chart" style={{ height }}>
      <svg width={chartWidth} height={chartHeight} className="chart__svg">
        {/* Zero line */}
        <line x1="0" y1={midline} x2={chartWidth} y2={midline} stroke="#999" strokeDasharray="4" />

        {/* Histogram bars */}
        {data.map((d, i) => {
          const x = i * 10;
          const y = scaleValue(d.histogram);
          const barHeight = Math.abs(y - midline);
          const color = d.histogram >= 0 ? '#22c55e' : '#ef4444';

          return (
            <rect
              key={`histogram-${i}`}
              x={x - 2}
              y={Math.min(y, midline)}
              width="4"
              height={barHeight}
              fill={color}
              opacity="0.3"
            />
          );
        })}

        {/* MACD line */}
        {data.length > 1 && (
          <polyline
            points={data.map((d, i) => `${i * 10},${scaleValue(d.macd)}`).join(' ')}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
          />
        )}

        {/* Signal line */}
        {data.length > 1 && (
          <polyline
            points={data.map((d, i) => `${i * 10},${scaleValue(d.signal)}`).join(' ')}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="2"
            strokeDasharray="4"
          />
        )}
      </svg>

      {/* Legend */}
      <div className="chart__legend">
        <div className="chart__legend-item">
          <div className="chart__legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
          <span>MACD</span>
        </div>
        <div className="chart__legend-item">
          <div className="chart__legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
          <span>Signal</span>
        </div>
      </div>
    </div>
  );
}
