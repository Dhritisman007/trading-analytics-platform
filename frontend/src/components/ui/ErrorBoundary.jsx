// src/components/ui/ErrorBoundary.jsx

import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding:      '2rem',
          textAlign:    'center',
          color:        'var(--color-text-secondary)',
        }}>
          <p style={{
            fontSize:   '16px',
            fontWeight: '500',
            color:      'var(--color-text-primary)',
            marginBottom: '8px',
          }}>
            Something went wrong
          </p>
          <p style={{ fontSize: '12px', marginBottom: '16px' }}>
            {this.state.error?.message}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding:      '6px 16px',
              fontSize:     '12px',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-md)',
              background:   'var(--color-background-secondary)',
              color:        'var(--color-text-secondary)',
              cursor:       'pointer',
            }}
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}