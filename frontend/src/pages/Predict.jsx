// src/pages/Predict.jsx

import { useState }        from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usePredict }      from '../hooks/usePredict'

import SignalCard           from '../components/panels/SignalCard'
import FeatureChart         from '../components/charts/FeatureChart'
import CategoryBreakdown    from '../components/panels/CategoryBreakdown'
import ExplanationTabs      from '../components/panels/ExplanationTabs'
import ModelPerformanceCard from '../components/panels/ModelPerformanceCard'
import ComparePanel         from '../components/panels/ComparePanel'
import SymbolSelector       from '../components/ui/SymbolSelector'
import { LoadingSpinner }   from '../components/ui/LoadingSpinner'
import { ErrorMessage }     from '../components/ui/ErrorMessage'
import { predictApi }       from '../api/endpoints'

export default function Predict() {
  const [symbol, setSymbol] = useState('^NSEI')
  const queryClient         = useQueryClient()

  const {
    data:      prediction,
    isLoading,
    error,
    refetch,
  } = usePredict(symbol)

  // Train mutation
  const trainMutation = useMutation({
    mutationFn: () => predictApi.train(symbol, '2y'),
    onSuccess:  () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['predict', symbol] })
        refetch()
      }, 15000)  // wait 15s for training to complete
    },
  })

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
          <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 3px' }}>
            ML Predictions
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
            Random Forest · 29 features · trained on 2 years of daily data
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <SymbolSelector
            symbol={symbol}
            period="2y"
            onSymbolChange={setSymbol}
            onPeriodChange={() => {}}
          />
          <button
            onClick={() => trainMutation.mutate()}
            disabled={trainMutation.isPending}
            style={{
              fontSize:     '12px',
              padding:      '6px 14px',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-md)',
              background:   'var(--color-background-secondary)',
              color:        'var(--color-text-secondary)',
              cursor:       trainMutation.isPending ? 'wait' : 'pointer',
            }}
          >
            {trainMutation.isPending ? 'Training...' : 'Retrain model'}
          </button>
        </div>
      </div>

      {/* Training message */}
      {trainMutation.isPending && (
        <div style={{
          padding:      '10px 14px',
          background:   'var(--color-background-secondary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-md)',
          fontSize:     '12px',
          color:        'var(--color-text-secondary)',
          marginBottom: '10px',
        }}>
          Training model on 2 years of Nifty 50 data...
          this takes about 10–15 seconds.
        </div>
      )}

      {isLoading && <LoadingSpinner />}
      {error     && <ErrorMessage message={error.message} onRetry={refetch} />}

      {prediction && (
        <>
          {/* ── Signal hero card ──────────────────────────────────── */}
          <SignalCard prediction={prediction} />

          {/* ── Two column layout ─────────────────────────────────── */}
          <div style={{
            display:             'grid',
            gridTemplateColumns: '1fr 1fr',
            gap:                 '10px',
            marginBottom:        '10px',
          }}>

            {/* Feature importance chart */}
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
                Feature contributions
              </p>
              <FeatureChart chartData={prediction.chart_data} />
            </div>

            {/* Category breakdown */}
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
                Indicator group impact
              </p>
              <CategoryBreakdown
                categorySummary={prediction.category_summary}
              />
            </div>
          </div>

          {/* ── Explanation tabs ───────────────────────────────────── */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '1rem 1.25rem',
            marginBottom: '10px',
          }}>
            <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 12px' }}>
              Why this signal?
            </p>
            <ExplanationTabs explanation={prediction.explanation} />
          </div>

          {/* ── Model performance ──────────────────────────────────── */}
          <ModelPerformanceCard modelInfo={prediction.model_info} />

          {/* ── Compare all symbols ────────────────────────────────── */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '1rem 1.25rem',
            marginTop:    '10px',
          }}>
            <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 12px' }}>
              All symbols comparison
            </p>
            <ComparePanel />
          </div>
        </>
      )}
    </div>
  )
}