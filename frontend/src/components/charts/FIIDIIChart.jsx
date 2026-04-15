/**
 * Component: FIIDIIChart
 * FII/DII flow chart
 */

import React from 'react';
import './FIIDIIChart.css';

export function FIIDIIChart({ 
  data = [],
  height = 300,
}) {
  if (!data || data.length === 0) {
    return (
      <div className="chart chart--empty" style={{ height }}>
        <p>No FII/DII data available</p>
      </div>
    );
  }

  const chartWidth = data.length * 15;
  const chartHeight = height - 40;
  const midline = chartHeight / 2;

  const maxFlow = Math.max(...data.map(d => Math.abs(d.fii_net)), ...data.map(d => Math.abs(d.dii_net)));
  const scale = chartHeight / (maxFlow * 2);

  return (
    <div className="chart fiidii-chart" style={{ height }}>
      <svg width={chartWidth} height={chartHeight} className="chart__svg">
        {/* Zero line */}
        <line x1="0" y1={midline} x2={chartWidth} y2={midline} stroke="#999" strokeDasharray="4" />

        {/* FII bars */}
        {data.map((d, i) => {
          const x = i * 15;
          const height = Math.abs(d.fii_net) * scale;
          const y = d.fii_net >= 0 ? midline - height : midline;
          const color = d.fii_net >= 0 ? '#22c55e' : '#ef4444';

          return (
            <rect
              key={`fii-${i}`}
              x={x}
              y={y}
              width="6"
              height={height || 1}
              fill={color}
              opacity="0.7"
              title={`FII: ${d.fii_net}`}
            />
          );
        })}

        {/* DII bars */}
        {data.map((d, i) => {
          const x = i * 15 + 7;
          const height = Math.abs(d.dii_net) * scale;
          const y = d.dii_net >= 0 ? midline - height : midline;
          const color = d.dii_net >= 0 ? '#3b82f6' : '#f59e0b';

          return (
            <rect
              key={`dii-${i}`}
              x={x}
              y={y}
              width="6"
              height={height || 1}
              fill={color}
              opacity="0.7"
              title={`DII: ${d.dii_net}`}
            />
          );
        })}
      </svg>

      {/* Legend */}
      <div className="chart__legend">
        <div className="chart__legend-item">
          <div className="chart__legend-color" style={{ backgroundColor: '#22c55e' }}></div>
          <span>FII Buy</span>
        </div>
        <div className="chart__legend-item">
          <div className="chart__legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
          <span>DII Buy</span>
        </div>
      </div>
    </div>
  );
}
