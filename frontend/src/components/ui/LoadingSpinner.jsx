// src/components/ui/LoadingSpinner.jsx
export const LoadingSpinner = ({ size = 24 }) => (
  <div style={{
    display:        'flex',
    justifyContent: 'center',
    alignItems:     'center',
    padding:        '2rem',
  }}>
    <div style={{
      width:        size,
      height:       size,
      border:       '2px solid var(--color-border-tertiary)',
      borderTop:    '2px solid var(--color-text-secondary)',
      borderRadius: '50%',
      animation:    'spin 0.8s linear infinite',
    }} />
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
)