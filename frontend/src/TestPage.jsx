// Quick test page to debug issues
export default function TestPage() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>✅ Frontend is working!</h1>
      <p>If you see this page, React and Vite are properly configured.</p>
      
      <div style={{ marginTop: '2rem', padding: '1rem', background: '#f0f0f0', borderRadius: '8px' }}>
        <h2>CSS Variables Test</h2>
        <p style={{ color: 'var(--color-text-primary)' }}>Text color (should be dark)</p>
        <p style={{ color: 'var(--color-text-secondary)' }}>Secondary text (should be gray)</p>
        <div style={{ 
          background: 'var(--color-background-primary)', 
          padding: '1rem', 
          borderRadius: '8px',
          border: '1px solid var(--color-border-primary)'
        }}>
          Box with CSS variables
        </div>
      </div>

      <div style={{ marginTop: '2rem', padding: '1rem', background: '#e8f5e9', borderRadius: '8px' }}>
        <h2>Colors Test</h2>
        <span style={{ background: '#22c55e', color: 'white', padding: '4px 8px', borderRadius: '4px' }}>Success (green)</span>
        <span style={{ background: '#ef4444', color: 'white', padding: '4px 8px', borderRadius: '4px', marginLeft: '8px' }}>Error (red)</span>
        <span style={{ background: '#3b82f6', color: 'white', padding: '4px 8px', borderRadius: '4px', marginLeft: '8px' }}>Info (blue)</span>
      </div>

      <div style={{ marginTop: '2rem', padding: '1rem', background: '#fff3cd', borderRadius: '8px' }}>
        <h2>Next Steps</h2>
        <ol>
          <li>Check browser console (F12) for any errors</li>
          <li>Verify API is running: <code>curl http://localhost:8000/health</code></li>
          <li>Check network tab to see API responses</li>
        </ol>
      </div>
    </div>
  )
}
