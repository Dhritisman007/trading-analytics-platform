// src/components/ui/ErrorMessage.jsx
export const ErrorMessage = ({ message, onRetry = null }) => (
  <div style={{
    padding:      '1rem',
    background:   'var(--color-background-danger)',
    border:       '0.5px solid var(--color-border-danger)',
    borderRadius: 'var(--border-radius-md)',
    color:        'var(--color-text-danger)',
    fontSize:     '13px',
  }}>
    <p style={{ margin: '0 0 8px' }}>{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        style={{
          fontSize:     '12px',
          padding:      '4px 12px',
          border:       '0.5px solid var(--color-border-danger)',
          borderRadius: 'var(--border-radius-md)',
          background:   'transparent',
          color:        'var(--color-text-danger)',
          cursor:       'pointer',
        }}
      >
        Retry
      </button>
    )}
  </div>
)