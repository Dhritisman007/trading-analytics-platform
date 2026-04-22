// src/components/panels/ModelPerformanceCard.jsx

import { formatNumber } from '../../utils/formatters'

const MetricBar = ({ label, value, max = 100, color = '#378ADD', unit = '%' }) => {
  const pct = Math.min((value / max) * 100, 100)
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        fontSize:       '11px',
        marginBottom:   '4px',
        color:          'var(--color-text-secondary)',
      }}>
        <span>{label}</span>
        <span style={{ fontWeight: '500', color: 'var(--color-text-primary)' }}>
          {formatNumber(value)}{unit}
        </span>
      </div>
      <div style={{
        height:       '6px',
        background:   'var(--color-background-secondary)',
        borderRadius: '3px',
        overflow:     'hidden',
      }}>
        <div style={{
          width:        `${pct}%`,
          height:       '100%',
          background:   color,
          borderRadius: '3px',
          transition:   'width 0.8s ease-out',
        }} />
      </div>
    </div>
  )
}

export default function ModelPerformanceCard({ modelInfo }) {
  if (!modelInfo) return null

  const {
    accuracy,
    precision,
    recall,
    f1_score,
    train_rows,
    train_period,
    trained_at,
  } = modelInfo

  const gradeColor =
    accuracy >= 60 ? '#1D9E75' :
    accuracy >= 55 ? '#BA7517' : '#E24B4A'

  return (
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
          Model performance
        </p>
        <span style={{
          fontSize:     '13px',
          fontWeight:   '500',
          color:        gradeColor,
          background:   `${gradeColor}18`,
          padding:      '3px 10px',
          borderRadius: '20px',
        }}>
          {accuracy}% accuracy
        </span>
      </div>

      <MetricBar label="Accuracy"  value={accuracy}  color="#378ADD" />
      <MetricBar label="Precision" value={precision} color="#1D9E75" />
      <MetricBar label="Recall"    value={recall}    color="#7F77DD" />
      <MetricBar label="F1 Score"  value={f1_score}  color="#BA7517" />

      <div style={{
        marginTop:   '12px',
        paddingTop:  '10px',
        borderTop:   '0.5px solid var(--color-border-tertiary)',
        fontSize:    '11px',
        color:       'var(--color-text-tertiary)',
        display:     'flex',
        flexDirection: 'column',
        gap:         '3px',
      }}>
        <span>Trained on {train_rows} candles · {train_period}</span>
        <span>Last trained: {trained_at
          ? new Date(trained_at).toLocaleDateString('en-IN')
          : '—'}
        </span>
      </div>

      {/* Disclaimer */}
      <div style={{
        marginTop:    '10px',
        padding:      '8px 10px',
        background:   'var(--color-background-secondary)',
        borderRadius: 'var(--border-radius-md)',
        fontSize:     '10px',
        color:        'var(--color-text-tertiary)',
        lineHeight:   '1.5',
      }}>
        For educational purposes only. Past indicator patterns do not guarantee
        future price movements. Never trade solely based on ML predictions.
      </div>
    </div>
  )
}