// src/components/panels/ComparePanel.jsx

import { useQuery } from '@tanstack/react-query'
import { predictApi } from '../../api/endpoints'
import { LoadingSpinner } from '../ui/LoadingSpinner'

export default function ComparePanel() {
  const { data, isLoading } = useQuery({
    queryKey:  ['predict-compare'],
    queryFn:   predictApi.compare,
    staleTime: 15 * 60 * 1000,
  })

  if (isLoading) return <LoadingSpinner size={20} />
  if (!data?.symbols) return null

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
      gap:     '8px',
    }}>
      {data.symbols.map((item) => {
        if (item.error) return null
        const isBuy = item.signal === 'BUY'

        return (
          <div key={item.symbol} style={{
            background:   'var(--color-background-secondary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-md)',
            padding:      '12px 14px',
          }}>
            <p style={{
              fontSize:   '11px',
              color:      'var(--color-text-secondary)',
              margin:     '0 0 4px',
            }}>
              {item.name}
            </p>

            <div style={{
              display:     'flex',
              alignItems:  'center',
              gap:         '8px',
              marginBottom: '6px',
            }}>
              <span style={{
                fontSize:     '16px',
                fontWeight:   '500',
                padding:      '3px 12px',
                borderRadius: '20px',
                background:   isBuy ? '#E1F5EE' : '#FCEBEB',
                color:        isBuy ? '#085041' : '#791F1F',
              }}>
                {item.signal}
              </span>
              <span style={{
                fontSize: '12px',
                color:    'var(--color-text-secondary)',
              }}>
                {item.confidence}%
              </span>
            </div>

            {/* Mini confidence bar */}
            <div style={{
              height:       '4px',
              background:   'var(--color-background-primary)',
              borderRadius: '2px',
              overflow:     'hidden',
              marginBottom: '6px',
            }}>
              <div style={{
                width:        `${item.confidence}%`,
                height:       '100%',
                background:   isBuy ? '#1D9E75' : '#E24B4A',
                borderRadius: '2px',
              }} />
            </div>

            <p style={{
              fontSize:   '10px',
              color:      'var(--color-text-tertiary)',
              margin:     0,
              lineHeight: '1.4',
            }}>
              RSI: {item.rsi} · {item.rsi_signal}
            </p>
          </div>
        )
      })}
    </div>
  )
}