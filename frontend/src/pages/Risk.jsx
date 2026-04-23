// src/pages/Risk.jsx

import { useState }    from 'react'
import { useMutation } from '@tanstack/react-query'
import { riskApi }     from '../api/endpoints'

import RiskForm       from '../components/panels/RiskForm'
import RiskResultCard from '../components/panels/RiskResultCard'
import { ErrorMessage } from '../components/ui/ErrorMessage'

export default function Risk() {
  const [symbol, setSymbol] = useState('^NSEI')
  const [result, setResult] = useState(null)

  const mutation = useMutation({
    mutationFn: (params) => riskApi.analyze({
      ...params,
      symbol,
    }),
    onSuccess: (data) => setResult(data),
  })

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 3px' }}>
          Risk Management
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
          Position sizing · R:R calculator · trade scoring
        </p>
      </div>

      <div style={{
        display:             'grid',
        gridTemplateColumns: '320px 1fr',
        gap:                 '16px',
        alignItems:          'start',
      }}>

        {/* Left — input form */}
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem 1.25rem',
        }}>
          <div style={{
            display:        'flex',
            justifyContent: 'space-between',
            alignItems:     'center',
            marginBottom:   '14px',
          }}>
            <p style={{ fontSize: '13px', fontWeight: '500', margin: 0 }}>
              Trade parameters
            </p>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              style={{
                fontSize:     '11px',
                padding:      '4px 8px',
                border:       '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-md)',
                background:   'var(--color-background-secondary)',
                color:        'var(--color-text-primary)',
              }}
            >
              <option value="^NSEI">Nifty 50</option>
              <option value="^BSESN">Sensex</option>
              <option value="^NSEBANK">Bank Nifty</option>
            </select>
          </div>

          <RiskForm
            onSubmit={mutation.mutate}
            isLoading={mutation.isPending}
          />

          {mutation.isError && (
            <div style={{ marginTop: '10px' }}>
              <ErrorMessage
                message={mutation.error?.message}
                onRetry={() => mutation.reset()}
              />
            </div>
          )}

          {/* Quick tips */}
          <div style={{
            marginTop:    '14px',
            paddingTop:   '12px',
            borderTop:    '0.5px solid var(--color-border-tertiary)',
            fontSize:     '11px',
            color:        'var(--color-text-tertiary)',
            lineHeight:   '1.6',
          }}>
            <p style={{ fontWeight: '500', margin: '0 0 4px', color: 'var(--color-text-secondary)' }}>
              Quick guide
            </p>
            <p style={{ margin: '0 0 3px' }}>· Risk 1% per trade (₹5,000 on ₹5L capital)</p>
            <p style={{ margin: '0 0 3px' }}>· Look for at least 1:2 R:R ratio</p>
            <p style={{ margin: '0 0 3px' }}>· Set stop loss at 1.5× ATR below entry</p>
            <p style={{ margin: 0 }}>· Grade B or above before entering</p>
          </div>
        </div>

        {/* Right — results */}
        <div>
          {!result && !mutation.isPending && (
            <div style={{
              height:         '300px',
              display:        'flex',
              alignItems:     'center',
              justifyContent: 'center',
              background:     'var(--color-background-primary)',
              border:         '0.5px solid var(--color-border-tertiary)',
              borderRadius:   'var(--border-radius-lg)',
              color:          'var(--color-text-tertiary)',
              fontSize:       '13px',
            }}>
              Enter trade parameters and click Calculate
            </div>
          )}

          {mutation.isPending && (
            <div style={{
              height:         '300px',
              display:        'flex',
              alignItems:     'center',
              justifyContent: 'center',
              background:     'var(--color-background-primary)',
              border:         '0.5px solid var(--color-border-tertiary)',
              borderRadius:   'var(--border-radius-lg)',
              color:          'var(--color-text-tertiary)',
              fontSize:       '13px',
            }}>
              Calculating...
            </div>
          )}

          {result && (
            <div style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-lg)',
              padding:      '1rem 1.25rem',
            }}>
              <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
                Analysis results
              </p>
              <p style={{
                fontSize:     '12px',
                color:        'var(--color-text-secondary)',
                margin:       '0 0 14px',
                fontWeight:   '500',
              }}>
                {result.summary}
              </p>
              <RiskResultCard result={result} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}