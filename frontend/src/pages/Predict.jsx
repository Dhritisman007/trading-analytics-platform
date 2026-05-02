// src/pages/Predict.jsx

import { useState }        from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usePredict }      from '../hooks/usePredict'
import { usePatterns, useLSTMPrediction, useTrainLSTM } from '../hooks/usePatterns'

import PatternCard       from '../components/panels/PatternCard'
import GPTCommentaryCard from '../components/panels/GPTCommentaryCard'

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
  const [period, setPeriod] = useState('2y')
  const queryClient         = useQueryClient()

  const {
    data:      prediction,
    isLoading,
    error,
    refetch,
  } = usePredict(symbol)

  // Train mutation
  const trainMutation = useMutation({
    mutationFn: () => predictApi.train(symbol, period),
    onSuccess:  () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['predict', symbol] })
        refetch()
      }, 15000)
    },
  })

  // Phase E features
  const { data: patterns }     = usePatterns(symbol)
  const { data: lstmData, error: lstmError } = useLSTMPrediction(symbol)
  const trainLSTM              = useTrainLSTM()

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
            period={period}
            onSymbolChange={setSymbol}
            onPeriodChange={setPeriod}
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
          Training model on {period} of data for {symbol}...
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

          {/* GPT Commentary */}
          <GPTCommentaryCard symbol={symbol} />
          
          {/* LSTM Prediction */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '1rem 1.25rem',
            marginTop:    '10px',
          }}>
            <div style={{
              display:        'flex',
              justifyContent: 'space-between',
              alignItems:     'center',
              marginBottom:   '12px',
            }}>
              <div>
                <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 2px' }}>
                  LSTM Neural Network
                </p>
                <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', margin: 0 }}>
                  Sequence model — learns from 30-day price patterns
                </p>
              </div>
              <button
                onClick={() => trainLSTM.mutate(symbol)}
                disabled={trainLSTM.isPending}
                style={{
                  fontSize:     '11px',
                  padding:      '5px 12px',
                  border:       '0.5px solid var(--color-border-tertiary)',
                  borderRadius: 'var(--border-radius-md)',
                  background:   'var(--color-background-secondary)',
                  color:        'var(--color-text-secondary)',
                  cursor:       trainLSTM.isPending ? 'wait' : 'pointer',
                }}
              >
                {trainLSTM.isPending ? 'Training (~3 min)...' : 'Train LSTM'}
              </button>
            </div>
          
            {lstmError ? (
              <div style={{
                padding:      '10px 12px',
                background:   'var(--color-background-secondary)',
                borderRadius: 'var(--border-radius-md)',
                fontSize:     '12px',
                color:        'var(--color-text-tertiary)',
              }}>
                LSTM model not trained yet. Click "Train LSTM" to train it (~3 minutes).
              </div>
            ) : lstmData ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
                  <span style={{
                    fontSize:     '22px',
                    fontWeight:   '500',
                    padding:      '6px 16px',
                    borderRadius: 'var(--border-radius-md)',
                    background:   lstmData.signal === 'BUY' ? '#E1F5EE' : '#FCEBEB',
                    color:        lstmData.signal === 'BUY' ? '#085041' : '#791F1F',
                  }}>
                    {lstmData.signal}
                  </span>
                  <div>
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 2px' }}>
                      {lstmData.confidence}% confidence · {lstmData.strength}
                    </p>
                    <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', margin: 0 }}>
                      Prob up: {lstmData.prob_up}% · Prob down: {lstmData.prob_down}%
                    </p>
                  </div>
                </div>
          
                {/* Probability bar */}
                <div style={{
                  height:       '8px',
                  borderRadius: '4px',
                  overflow:     'hidden',
                  background:   '#E24B4A40',
                  marginBottom: '6px',
                }}>
                  <div style={{
                    width:        `${lstmData.prob_up}%`,
                    height:       '100%',
                    background:   '#1D9E75',
                    borderRadius: '4px',
                    transition:   'width 1s',
                  }} />
                </div>
                <div style={{
                  display:        'flex',
                  justifyContent: 'space-between',
                  fontSize:       '10px',
                  color:          'var(--color-text-tertiary)',
                  marginBottom:   '8px',
                }}>
                  <span style={{ color: '#1D9E75' }}>↑ Up {lstmData.prob_up}%</span>
                  <span style={{ color: '#E24B4A' }}>↓ Down {lstmData.prob_down}%</span>
                </div>
          
                <p style={{
                  fontSize:   '11px',
                  color:      'var(--color-text-secondary)',
                  margin:     0,
                  lineHeight: '1.5',
                }}>
                  {lstmData.description}
                </p>
              </div>
            ) : null}
          </div>
          
          {/* Candlestick Patterns */}
          <div style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding:      '1rem 1.25rem',
            marginTop:    '10px',
          }}>
            <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 12px' }}>
              Candlestick Pattern Detection
            </p>
            <PatternCard
              patterns={patterns?.patterns || []}
              summary={patterns?.summary  || {}}
            />
          </div>
        </>
      )}
    </div>
  )
}