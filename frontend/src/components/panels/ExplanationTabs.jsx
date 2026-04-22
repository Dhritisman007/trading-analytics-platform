// src/components/panels/ExplanationTabs.jsx

import { useState } from 'react'

const TABS = [
  { key: 'one_line',  label: 'Summary' },
  { key: 'simple',    label: 'Simple' },
  { key: 'technical', label: 'Technical' },
]

export default function ExplanationTabs({ explanation }) {
  const [active, setActive] = useState('simple')
  if (!explanation) return null

  return (
    <div>
      {/* Tab row */}
      <div style={{
        display:      'flex',
        gap:          '4px',
        marginBottom: '10px',
      }}>
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActive(key)}
            style={{
              fontSize:     '11px',
              padding:      '4px 12px',
              borderRadius: '20px',
              border:       '0.5px solid var(--color-border-tertiary)',
              background:   active === key
                ? 'var(--color-text-primary)'
                : 'var(--color-background-secondary)',
              color: active === key
                ? 'var(--color-background-primary)'
                : 'var(--color-text-secondary)',
              cursor:     'pointer',
              fontWeight: active === key ? '500' : '400',
              transition: 'all 0.15s',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <p style={{
        fontSize:   '13px',
        color:      'var(--color-text-secondary)',
        lineHeight: '1.7',
        margin:     0,
        fontFamily: active === 'technical'
          ? 'var(--font-mono)'
          : 'inherit',
        fontSize: active === 'technical' ? '12px' : '13px',
      }}>
        {explanation[active] || '—'}
      </p>
    </div>
  )
}