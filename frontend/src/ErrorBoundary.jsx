import { Component } from 'react'

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
    })
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          fontFamily: 'monospace',
          background: '#ffebee',
          color: '#c62828',
          minHeight: '100vh',
        }}>
          <h1>❌ Application Error</h1>
          <pre style={{
            background: '#fff3e0',
            padding: '1rem',
            borderRadius: '8px',
            overflowX: 'auto',
            color: '#e65100',
          }}>
            {this.state.error?.toString()}
          </pre>
          <details style={{ marginTop: '1rem' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Stack trace</summary>
            <pre style={{
              background: '#fff3e0',
              padding: '1rem',
              borderRadius: '8px',
              overflowX: 'auto',
              color: '#e65100',
              marginTop: '0.5rem',
            }}>
              {this.state.errorInfo?.componentStack}
            </pre>
          </details>
          <button 
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              background: '#1976d2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Reload Page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
