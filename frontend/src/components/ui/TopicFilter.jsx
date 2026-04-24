// src/components/ui/TopicFilter.jsx

import { TOPICS } from '../../utils/constants'

export default function TopicFilter({ active, onChange }) {
  return (
    <div style={{
      display:  'flex',
      gap:      '5px',
      flexWrap: 'wrap',
    }}>
      <button
        onClick={() => onChange(null)}
        style={{
          fontSize:     '11px',
          padding:      '4px 10px',
          borderRadius: '20px',
          border:       '0.5px solid var(--color-border-tertiary)',
          background:   !active
            ? 'var(--color-text-primary)'
            : 'var(--color-background-secondary)',
          color:        !active
            ? 'var(--color-background-primary)'
            : 'var(--color-text-secondary)',
          cursor:     'pointer',
          fontWeight: !active ? '500' : '400',
        }}
      >
        All
      </button>

      {TOPICS.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => onChange(active === value ? null : value)}
          style={{
            fontSize:     '11px',
            padding:      '4px 10px',
            borderRadius: '20px',
            border:       '0.5px solid var(--color-border-tertiary)',
            background:   active === value
              ? 'var(--color-text-primary)'
              : 'var(--color-background-secondary)',
            color:        active === value
              ? 'var(--color-background-primary)'
              : 'var(--color-text-secondary)',
            cursor:     'pointer',
            fontWeight: active === value ? '500' : '400',
            transition: 'all 0.15s',
          }}
        >
          {label}
        </button>
      ))}
    </div>
  )
}