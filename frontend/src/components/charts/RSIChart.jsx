/**
 * Component: RSIChart
 * RSI technical indicator chart
 */

import React from 'react';
import './RSIChart.css';

export function RSIChart({ 
  data = [],
  height = 300,
}) {
  if (!data || data.length === 0) {
    return (
      <div className="chart chart--empty" style={{ height }}>
        <p>No RSI data available</p>
      </div>
    );
  }

  const chartWidth = data.length * 10;
  const chartHeight = height - 40;

  const scaleRSI = (rsi) => {
    return chartHeight - (rsi / 100) * chartHeight;
  };

  return (
    <div className="chart rsi-chart" style={{ height }}>
      <svg width={chartWidth} height={chartHeight} className="chart__svg">
        {/* Background zones */}
        <rect y="0" width={chartWidth} height={scaleRSI(70)} fill="#ffe5e5" opacity="0.3" />
        <rect y={scaleRSI(70)} width={chartWidth} height={scaleRSI(30) - scaleRSI(70)} fill="#f0f0f0" opacity="0.3" />
        <rect y={scaleRSI(30)} width={chartWidth} height={chartHeight - scaleRSI(30)} fill="#e5f5e5" opacity="0.3" />

        {/* Overbought/Oversold lines */}
        <line x1="0" y1={scaleRSI(70)} x2={chartWidth} y2={scaleRSI(70)} stroke="#ef4444" strokeDasharray="4" />
        <line x1="0" y1={scaleRSI(30)} x2={chartWidth} y2={scaleRSI(30)} stroke="#22c55e" strokeDasharray="4" />
        <line x1="0" y1={scaleRSI(50)} x2={chartWidth} y2={scaleRSI(50)} stroke="#999" strokeDasharray="4" opacity="0.5" />

        {/* RSI line */}
        {data.length > 1 && (
          <polyline
            points={data.map((d, i) => `${i * 10},${scaleRSI(d.rsi)}`).join(' ')}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
          />
        )}

        {/* Data points */}
        {data.map((d, i) => (
          <circle
            key={`rsi-${i}`}
            cx={i * 10}
            cy={scaleRSI(d.rsi)}
            r="2"
            fill="#3b82f6"
          />
        ))}
      </svg>

      {/* Labels */}
      <div className="chart__labels">
        <div className="chart__label" style={{ left: '5px' }}>Overbought (70)</div>
        <div className="chart__label" style={{ left: '5px', bottom: '30%' }}>Neutral (50)</div>
        <div className="chart__label" style={{ left: '5px', bottom: '5px' }}>Oversold (30)</div>
      </div>
    </div>
  );
}
