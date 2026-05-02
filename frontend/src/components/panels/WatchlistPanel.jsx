// src/components/panels/WatchlistPanel.jsx

import { useState }            from 'react'
import { Star, X, Plus }       from 'lucide-react'
import {
  useWatchlist,
  useAddToWatchlist,
  useRemoveFromWatchlist,
} from '../../hooks/useWatchlist'
import { SYMBOLS } from '../../utils/constants'

export default function WatchlistPanel({ onSelectSymbol, currentSymbol }) {
  const [adding, setAdding]       = useState(false)
  const [selected, setSelected]   = useState('^NSEI')

  const { data }                = useWatchlist()
  const addMutation             = useAddToWatchlist()
  const removeMutation          = useRemoveFromWatchlist()

  const items = data?.items || []

  const handleAdd = () => {
    addMutation.mutate(selected, {
      onSuccess: () => setAdding(false),
    })
  }

  return (
    <div style={{ marginBottom: '1rem' }}>
      {/* Header */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        marginBottom:   '8px',
        padding:        '0 4px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Star size={12} style={{ color: 'var(--color-text-tertiary)' }} />
          <span style={{ fontSize: '11px', fontWeight: '500', color: 'var(--color-text-secondary)' }}>
            Watchlist
          </span>
        </div>
        <button
          onClick={() => setAdding(!adding)}
          style={{
            display:        'flex',
            alignItems:     'center',
            justifyContent: 'center',
            width:          '18px',
            height:         '18px',
            borderRadius:   '50%',
            border:         '0.5px solid var(--color-border-tertiary)',
            background:     'transparent',
            color:          'var(--color-text-tertiary)',
            cursor:         'pointer',
            padding:        0,
          }}
        >
          <Plus size={10} />
        </button>
      </div>

      {/* Add symbol dropdown */}
      {adding && (
        <div style={{
          display:      'flex',
          gap:          '4px',
          marginBottom: '6px',
        }}>
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            style={{
              flex:         1,
              fontSize:     '11px',
              padding:      '4px 6px',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-md)',
              background:   'var(--color-background-secondary)',
              color:        'var(--color-text-primary)',
            }}
          >
            {SYMBOLS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          <button
            onClick={handleAdd}
            disabled={addMutation.isPending}
            style={{
              fontSize:     '10px',
              padding:      '4px 8px',
              borderRadius: 'var(--border-radius-md)',
              border:       'none',
              background:   'var(--color-text-primary)',
              color:        'var(--color-background-primary)',
              cursor:       'pointer',
            }}
          >
            Add
          </button>
        </div>
      )}

      {/* Watchlist items */}
      {items.length === 0 ? (
        <p style={{
          fontSize:  '11px',
          color:     'var(--color-text-tertiary)',
          padding:   '4px',
          textAlign: 'center',
        }}>
          No symbols — click + to add
        </p>
      ) : (
        items.map((item) => (
          <div
            key={item.symbol}
            onClick={() => onSelectSymbol?.(item.symbol)}
            style={{
              display:        'flex',
              justifyContent: 'space-between',
              alignItems:     'center',
              padding:        '5px 8px',
              borderRadius:   'var(--border-radius-md)',
              cursor:         'pointer',
              background:     currentSymbol === item.symbol
                ? 'var(--color-background-tertiary)'
                : 'transparent',
              marginBottom:   '2px',
            }}
            onMouseEnter={(e) => {
              if (currentSymbol !== item.symbol)
                e.currentTarget.style.background = 'var(--color-background-secondary)'
            }}
            onMouseLeave={(e) => {
              if (currentSymbol !== item.symbol)
                e.currentTarget.style.background = 'transparent'
            }}
          >
            <div>
              <p style={{
                fontSize:   '12px',
                fontWeight: '500',
                color:      'var(--color-text-primary)',
                margin:     0,
              }}>
                {item.name}
              </p>
              <p style={{
                fontSize: '9px',
                color:    'var(--color-text-tertiary)',
                margin:   0,
              }}>
                {item.symbol}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                removeMutation.mutate(item.symbol)
              }}
              style={{
                display:        'flex',
                alignItems:     'center',
                justifyContent: 'center',
                width:          '16px',
                height:         '16px',
                borderRadius:   '50%',
                border:         'none',
                background:     'transparent',
                color:          'var(--color-text-tertiary)',
                cursor:         'pointer',
                padding:        0,
                opacity:        0,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '1'
                e.currentTarget.style.color   = '#E24B4A'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '0'
              }}
            >
              <X size={10} />
            </button>
          </div>
        ))
      )}
    </div>
  )
}
