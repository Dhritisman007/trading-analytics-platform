// src/components/panels/NewsCard.jsx

import { formatDateTime } from '../../utils/formatters'

const ImpactDot = ({ impact }) => {
  const colors = {
    HIGH:   '#E24B4A',
    MEDIUM: '#BA7517',
    LOW:    '#888780',
  }
  return (
    <span style={{
      width:        '6px',
      height:       '6px',
      borderRadius: '50%',
      background:   colors[impact] || '#888780',
      display:      'inline-block',
      flexShrink:   0,
    }} />
  )
}

export default function NewsCard({ article }) {
  const {
    title,
    summary,
    source,
    url,
    published_at,
    is_breaking,
    topics     = [],
    sentiment  = {},
    impact     = {},
  } = article

  const sentColor = sentiment.label === 'positive' ? '#1D9E75'
                  : sentiment.label === 'negative' ? '#E24B4A'
                  : '#888780'

  return (
    <div style={{
      padding:      '12px 0',
      borderBottom: '0.5px solid var(--color-border-tertiary)',
    }}>
      {/* Top row — source + time + breaking */}
      <div style={{
        display:     'flex',
        alignItems:  'center',
        gap:         '8px',
        marginBottom: '5px',
        flexWrap:    'wrap',
      }}>
        <span style={{
          fontSize:   '10px',
          fontWeight: '500',
          color:      'var(--color-text-tertiary)',
        }}>
          {source}
        </span>

        <span style={{
          fontSize: '10px',
          color:    'var(--color-text-tertiary)',
        }}>
          {formatDateTime(published_at)}
        </span>

        {is_breaking && (
          <span style={{
            fontSize:     '9px',
            fontWeight:   '500',
            padding:      '1px 6px',
            borderRadius: '20px',
            background:   '#FCEBEB',
            color:        '#791F1F',
          }}>
            BREAKING
          </span>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: 'auto' }}>
          <ImpactDot impact={impact.impact} />
          <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>
            {impact.impact}
          </span>
        </div>
      </div>

      {/* Title */}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          fontSize:       '13px',
          fontWeight:     '500',
          color:          'var(--color-text-primary)',
          lineHeight:     '1.4',
          display:        'block',
          marginBottom:   '5px',
          textDecoration: 'none',
        }}
        onMouseOver={(e) => e.target.style.color = sentColor}
        onMouseOut={(e)  => e.target.style.color = 'var(--color-text-primary)'}
      >
        {title}
      </a>

      {/* Summary */}
      {summary && (
        <p style={{
          fontSize:     '11px',
          color:        'var(--color-text-secondary)',
          margin:       '0 0 6px',
          lineHeight:   '1.5',
        }}>
          {summary}
        </p>
      )}

      {/* Bottom row — sentiment + topics */}
      <div style={{
        display:    'flex',
        alignItems: 'center',
        gap:        '6px',
        flexWrap:   'wrap',
      }}>
        {/* Sentiment badge */}
        <span style={{
          fontSize:     '10px',
          fontWeight:   '500',
          padding:      '2px 8px',
          borderRadius: '20px',
          background:   `${sentColor}18`,
          color:        sentColor,
        }}>
          {sentiment.emoji} {sentiment.label} · {sentiment.compound}
        </span>

        {/* Topic tags */}
        {topics.slice(0, 3).map((topic) => (
          <span key={topic} style={{
            fontSize:     '10px',
            padding:      '2px 7px',
            borderRadius: '20px',
            background:   'var(--color-background-secondary)',
            color:        'var(--color-text-tertiary)',
            border:       '0.5px solid var(--color-border-tertiary)',
          }}>
            {topic.replace('_', ' ')}
          </span>
        ))}
      </div>
    </div>
  )
}