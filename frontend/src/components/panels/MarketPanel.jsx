/**
 * Component: MarketPanel
 * Market data display panel
 */

import React from 'react';
import { Card } from '../ui/Card';
import { StatCard } from '../ui/StatCard';
import { Badge } from '../ui/Badge';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { ErrorMessage } from '../ui/ErrorMessage';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import './MarketPanel.css';

export function MarketPanel({ data, loading, error, onRefresh }) {
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onDismiss={onRefresh} />;
  if (!data) return <Card><p>No market data</p></Card>;

  const changePercent = ((data.current - data.previous_close) / data.previous_close) * 100;
  const isUp = changePercent >= 0;

  return (
    <Card title="Market Overview" className="market-panel">
      <div className="market-panel__grid">
        <StatCard
          label="Current Price"
          value={formatCurrency(data.current)}
          changePercent={changePercent}
          color={isUp ? '#22c55e' : '#ef4444'}
          icon="📈"
        />
        <StatCard
          label="Day High"
          value={formatCurrency(data.high)}
          icon="📊"
        />
        <StatCard
          label="Day Low"
          value={formatCurrency(data.low)}
          icon="📉"
        />
        <StatCard
          label="Volume"
          value={formatNumber(data.volume)}
          unit="M"
          icon="📦"
        />
      </div>

      <div className="market-panel__details">
        <div className="market-panel__detail">
          <span className="market-panel__label">Previous Close:</span>
          <span className="market-panel__value">{formatCurrency(data.previous_close)}</span>
        </div>
        <div className="market-panel__detail">
          <span className="market-panel__label">Open:</span>
          <span className="market-panel__value">{formatCurrency(data.open)}</span>
        </div>
        <div className="market-panel__detail">
          <span className="market-panel__label">P/E Ratio:</span>
          <span className="market-panel__value">{data.pe_ratio?.toFixed(2) || 'N/A'}</span>
        </div>
        <div className="market-panel__detail">
          <span className="market-panel__label">Market Cap:</span>
          <span className="market-panel__value">{formatNumber(data.market_cap)}</span>
        </div>
      </div>

      <div className="market-panel__footer">
        <Badge 
          label={isUp ? '📈 Bullish' : '📉 Bearish'}
          variant={isUp ? 'success' : 'error'}
        />
        <button className="market-panel__refresh" onClick={onRefresh}>
          🔄 Refresh
        </button>
      </div>
    </Card>
  );
}
