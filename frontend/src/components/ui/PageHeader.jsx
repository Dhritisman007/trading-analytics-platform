// src/components/ui/PageHeader.jsx

export default function PageHeader({
  title,
  subtitle,
  children,  // right-side actions
}) {
  return (
    <div style={{
      display:        'flex',
      justifyContent: 'space-between',
      alignItems:     'flex-start',
      marginBottom:   '1.25rem',
      flexWrap:       'wrap',
      gap:            '10px',
    }}>
      <div>
        <h1 style={{
          fontSize:   '20px',
          fontWeight: '500',
          margin:     '0 0 3px',
          color:      'var(--color-text-primary)',
        }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{
            fontSize: '12px',
            color:    'var(--color-text-secondary)',
            margin:   0,
          }}>
            {subtitle}
          </p>
        )}
      </div>
      {children && (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {children}
        </div>
      )}
    </div>
  )
}
