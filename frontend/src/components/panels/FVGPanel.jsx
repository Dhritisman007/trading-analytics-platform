/**
 * Component: FVGPanel
 * Fair Value Gap pattern panel
 */

import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { formatCurrency } from '../../utils/formatters';
import './FVGPanel.css';

export function FVGPanel({ gaps = [], loading, error }) {
  if (loading) {
    return <Card title="Fair Value Gaps"><p>Loading FVGs...</p></Card>;
  }

  if (error) {
    return <Card title="Fair Value Gaps"><p className="error">{error}</p></Card>;
  }

  if (!gaps || gaps.length === 0) {
    return <Card title="Fair Value Gaps"><p>No FVG patterns detected</p></Card>;
  }

  return (
    <Card title={`Fair Value Gaps (${gaps.length})`} className="fvg-panel">
      <div className="fvg-panel__list">
        {gaps.slice(0, 5).map((gap, idx) => (
          <div key={idx} className="fvg-panel__item">
            <div className="fvg-panel__header">
              <h4 className="fvg-panel__title">{gap.type} FVG</h4>
              <Badge
                label={gap.status}
                variant={gap.status === 'filled' ? 'info' : 'warning'}
                size="sm"
              />
            </div>

            <div className="fvg-panel__details">
              <div className="fvg-panel__detail">
                <span className="fvg-panel__label">Top:</span>
                <span className="fvg-panel__value">{formatCurrency(gap.top)}</span>
              </div>
              <div className="fvg-panel__detail">
                <span className="fvg-panel__label">Bottom:</span>
                <span className="fvg-panel__value">{formatCurrency(gap.bottom)}</span>
              </div>
              <div className="fvg-panel__detail">
                <span className="fvg-panel__label">Break Level:</span>
                <span className="fvg-panel__value">{formatCurrency(gap.break_level)}</span>
              </div>
              <div className="fvg-panel__detail">
                <span className="fvg-panel__label">Size:</span>
                <span className="fvg-panel__value">{formatCurrency(gap.size)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
