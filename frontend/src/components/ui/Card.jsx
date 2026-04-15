// src/components/ui/Card.jsx
export const Card = ({ children, className = '', title = null }) => (
  <div
    className={className}
    style={{
      background:    'var(--color-background-primary)',
      border:        '0.5px solid var(--color-border-tertiary)',
      borderRadius:  'var(--border-radius-lg)',
      padding:       '1rem 1.25rem',
    }}
  >
    {title && (
      <p style={{
        fontSize:     '13px',
        fontWeight:   '500',
        color:        'var(--color-text-primary)',
        marginBottom: '12px',
      }}>
        {title}
      </p>
    )}
    {children}
  </div>
)