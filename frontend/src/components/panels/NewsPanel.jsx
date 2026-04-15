/**
 * Component: NewsPanel
 * News and sentiment display panel
 */

import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { formatDate, formatTimeAgo, getSentimentColor } from '../../utils/formatters';
import './NewsPanel.css';

export function NewsPanel({ articles = [], loading, error }) {
  if (loading) {
    return <Card title="Latest News"><p>Loading news...</p></Card>;
  }

  if (error) {
    return <Card title="Latest News"><p className="error">{error}</p></Card>;
  }

  if (!articles || articles.length === 0) {
    return <Card title="Latest News"><p>No news available</p></Card>;
  }

  return (
    <Card title={`Latest News (${articles.length})`} className="news-panel">
      <div className="news-panel__list">
        {articles.slice(0, 5).map((article, idx) => (
          <article key={idx} className="news-panel__item">
            <div className="news-panel__header">
              <h4 className="news-panel__title">{article.title}</h4>
              <Badge
                label={article.sentiment_label}
                variant={article.sentiment_label}
                size="sm"
              />
            </div>
            <p className="news-panel__summary">{article.summary}</p>
            <div className="news-panel__footer">
              <span className="news-panel__source">{article.source}</span>
              <span className="news-panel__time">{formatTimeAgo(article.published_at)}</span>
            </div>
          </article>
        ))}
      </div>

      <button className="news-panel__viewall">
        View All News →
      </button>
    </Card>
  );
}
