// src/pages/News.jsx

import { useState }          from 'react'
import { useNews, useMarketMood } from '../hooks/useNews'
import { useFiiDii }         from '../hooks/useFiiDii'

import NewsCard           from '../components/panels/NewsCard'
import FIIDIIChart        from '../components/charts/FIIDIIChart'
import FIIDIISummaryCard  from '../components/panels/FIIDIISummaryCard'
import MarketMoodBadge    from '../components/ui/MarketMoodBadge'
import TopicFilter        from '../components/ui/TopicFilter'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage }   from '../components/ui/ErrorMessage'
import { NEWS_SOURCES }   from '../utils/constants'

const SentimentFilter = ({ active, onChange }) => {
  const opts = [
    { value: null,       label: 'All',      color: 'var(--color-text-secondary)' },
    { value: 'positive', label: 'Positive', color: '#1D9E75' },
    { value: 'neutral',  label: 'Neutral',  color: '#888780' },
    { value: 'negative', label: 'Negative', color: '#E24B4A' },
  ]
  return (
    <div style={{ display: 'flex', gap: '5px' }}>
      {opts.map(({ value, label, color }) => (
        <button
          key={label}
          onClick={() => onChange(value)}
          style={{
            fontSize:     '11px',
            padding:      '3px 10px',
            borderRadius: '20px',
            border:       `0.5px solid ${active === value ? color : 'var(--color-border-tertiary)'}`,
            background:   active === value ? `${color}18` : 'transparent',
            color:        active === value ? color : 'var(--color-text-secondary)',
            cursor:       'pointer',
            fontWeight:   active === value ? '500' : '400',
          }}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

export default function News() {
  const [topic,     setTopic]     = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [source,    setSource]    = useState(null)

  const {
    data:      newsData,
    isLoading: newsLoading,
    error:     newsError,
    refetch:   newsRefetch,
  } = useNews(40, topic, source)

  const { data: mood }    = useMarketMood()
  const { data: fiiData } = useFiiDii(30)

  // Client-side sentiment filter on top of topic + source filters
  const articles = (newsData?.articles || []).filter((a) =>
    (!sentiment || a.sentiment?.label === sentiment) &&
    (!source    || a.source === source)
  )

  return (
    <div>
      {/* ── Header ────────────────────────────────────────────────── */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'flex-start',
        marginBottom:   '1.25rem',
        flexWrap:       'wrap',
        gap:            '10px',
      }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 5px' }}>
            News & Institutional Flows
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
            Financial news · VADER sentiment · FII/DII daily flows
          </p>
        </div>

        {/* Market mood badge */}
        {mood?.market_mood && (
          <MarketMoodBadge mood={mood.market_mood} size="lg" />
        )}
      </div>

      {/* ── Two column layout ──────────────────────────────────────── */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: '1fr 340px',
        gap:                 '14px',
        alignItems:          'start',
      }}>

        {/* ── LEFT — News feed ──────────────────────────────────────── */}
        <div>
          {/* Filters */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '12px 14px',
            marginBottom: '10px',
          }}>
            <div style={{ marginBottom: '8px' }}>
              <p style={{
                fontSize:     '10px',
                fontWeight:   '500',
                color:        'var(--color-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                margin:       '0 0 6px',
              }}>
                Filter by topic
              </p>
              <TopicFilter active={topic} onChange={setTopic} />
            </div>
            <div>
              <p style={{
                fontSize:      '10px',
                fontWeight:    '500',
                color:         'var(--color-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                margin:        '0 0 6px',
              }}>
                Filter by sentiment
              </p>
              <SentimentFilter active={sentiment} onChange={setSentiment} />
            </div>
            <div>
              <p style={{
                fontSize:      '10px',
                fontWeight:    '500',
                color:         'var(--color-text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                margin:        '0 0 6px',
              }}>
                Filter by source
              </p>
              <div style={{
                display:  'flex',
                gap:      '6px',
                flexWrap: 'wrap',
              }}>
                {NEWS_SOURCES.map(({ value, label }) => (
                  <button
                    key={String(value)}
                    onClick={() => setSource(source === value ? null : value)}
                    style={{
                      fontSize:     '11px',
                      padding:      '4px 10px',
                      borderRadius: '20px',
                      border:       '0.5px solid var(--color-border-tertiary)',
                      background:   source === value
                        ? 'var(--color-text-primary)'
                        : 'var(--color-background-secondary)',
                      color: source === value
                        ? 'var(--color-background-primary)'
                        : 'var(--color-text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Stats row */}
          {newsData && (
            <div style={{
              display:             'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap:                 '6px',
              marginBottom:        '10px',
            }}>
              {[
                {
                  label: 'Total articles',
                  value: newsData.total_available,
                  color: 'var(--color-text-primary)',
                },
                {
                  label: 'Positive',
                  value: newsData.market_mood?.positive_count,
                  color: '#1D9E75',
                },
                {
                  label: 'Negative',
                  value: newsData.market_mood?.negative_count,
                  color: '#E24B4A',
                },
                {
                  label: 'Breaking',
                  value: newsData.breaking_count,
                  color: '#791F1F',
                },
              ].map(({ label, value, color }) => (
                <div key={label} style={{
                  background:   'var(--color-background-primary)',
                  border:       '0.5px solid var(--color-border-tertiary)',
                  borderRadius: 'var(--border-radius-md)',
                  padding:      '8px 10px',
                  textAlign:    'center',
                }}>
                  <p style={{
                    fontSize: '10px',
                    color:    'var(--color-text-secondary)',
                    margin:   '0 0 2px',
                  }}>
                    {label}
                  </p>
                  <p style={{
                    fontSize:   '18px',
                    fontWeight: '500',
                    color,
                    margin:     0,
                  }}>
                    {value ?? '—'}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* News list */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '0 14px',
          }}>
            {newsLoading && <LoadingSpinner />}
            {newsError   && (
              <div style={{ padding: '14px 0' }}>
                <ErrorMessage message={newsError.message} onRetry={newsRefetch} />
              </div>
            )}

            {articles.length === 0 && !newsLoading && (
              <p style={{
                textAlign: 'center',
                color:     'var(--color-text-tertiary)',
                fontSize:  '13px',
                padding:   '2rem 0',
              }}>
                No articles match the current filters
              </p>
            )}

            {articles.map((article, i) => (
              <NewsCard key={`${article.url}-${i}`} article={article} />
            ))}
          </div>
        </div>

        {/* ── RIGHT — FII/DII sidebar ───────────────────────────────── */}
        <div>

          {/* FII/DII summary */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '1rem 1.25rem',
            marginBottom: '10px',
          }}>
            <p style={{
              fontSize:     '13px',
              fontWeight:   '500',
              margin:       '0 0 14px',
            }}>
              FII / DII flows
            </p>

            {fiiData
              ? <FIIDIISummaryCard data={fiiData} />
              : <LoadingSpinner size={20} />
            }
          </div>

          {/* FII/DII chart */}
          {fiiData?.chart_data && (
            <div style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-lg)',
              padding:      '1rem 1.25rem',
              marginBottom: '10px',
            }}>
              <p style={{
                fontSize:     '13px',
                fontWeight:   '500',
                margin:       '0 0 12px',
              }}>
                30-day flow chart
              </p>

              {/* Legend */}
              <div style={{
                display:      'flex',
                gap:          '12px',
                marginBottom: '8px',
                fontSize:     '11px',
                color:        'var(--color-text-secondary)',
              }}>
                {[
                  { label: 'FII net', color: '#1D9E75' },
                  { label: 'DII net', color: '#378ADD' },
                ].map(({ label, color }) => (
                  <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{
                      width:      '10px',
                      height:     '3px',
                      background: color,
                      display:    'inline-block',
                      borderRadius: '1px',
                    }} />
                    {label}
                  </span>
                ))}
              </div>

              <FIIDIIChart chartData={fiiData.chart_data} height={180} />
            </div>
          )}

          {/* Topic distribution */}
          {newsData?.topic_distribution && (
            <div style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-lg)',
              padding:      '1rem 1.25rem',
            }}>
              <p style={{
                fontSize:     '13px',
                fontWeight:   '500',
                margin:       '0 0 12px',
              }}>
                Topics in today's news
              </p>

              {Object.entries(newsData.topic_distribution)
                .slice(0, 7)
                .map(([topic, count]) => {
                  const maxCount = Math.max(
                    ...Object.values(newsData.topic_distribution)
                  )
                  const pct = (count / maxCount) * 100

                  return (
                    <div key={topic} style={{ marginBottom: '8px' }}>
                      <div style={{
                        display:        'flex',
                        justifyContent: 'space-between',
                        fontSize:       '11px',
                        marginBottom:   '3px',
                      }}>
                        <span style={{ color: 'var(--color-text-secondary)' }}>
                          {topic.replace('_', ' ')}
                        </span>
                        <span style={{
                          color:      'var(--color-text-tertiary)',
                          fontWeight: '500',
                        }}>
                          {count}
                        </span>
                      </div>
                      <div style={{
                        height:       '4px',
                        background:   'var(--color-background-secondary)',
                        borderRadius: '2px',
                        overflow:     'hidden',
                      }}>
                        <div style={{
                          width:        `${pct}%`,
                          height:       '100%',
                          background:   '#7F77DD',
                          borderRadius: '2px',
                          opacity:      0.7,
                        }} />
                      </div>
                    </div>
                  )
                })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}