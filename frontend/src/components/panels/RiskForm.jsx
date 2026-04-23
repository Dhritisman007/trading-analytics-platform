// src/components/panels/RiskForm.jsx

import { useState } from 'react'

const InputField = ({ label, value, onChange, type = 'number', hint = '' }) => (
  <div style={{ marginBottom: '12px' }}>
    <label style={{
      display:    'block',
      fontSize:   '11px',
      color:      'var(--color-text-secondary)',
      marginBottom: '4px',
    }}>
      {label}
    </label>
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        width:        '100%',
        padding:      '7px 10px',
        fontSize:     '13px',
        border:       '0.5px solid var(--color-border-tertiary)',
        borderRadius: 'var(--border-radius-md)',
        background:   'var(--color-background-secondary)',
        color:        'var(--color-text-primary)',
        outline:      'none',
        boxSizing:    'border-box',
      }}
    />
    {hint && (
      <p style={{
        fontSize: '10px',
        color:    'var(--color-text-tertiary)',
        margin:   '3px 0 0',
      }}>
        {hint}
      </p>
    )}
  </div>
)

export default function RiskForm({ onSubmit, isLoading }) {
  const [form, setForm] = useState({
    capital:     '500000',
    entry_price: '',
    stop_loss:   '',
    target_price: '',
    risk_pct:    '1',
  })

  const set = (key) => (val) => setForm((p) => ({ ...p, [key]: val }))

  const handleSubmit = () => {
    const { capital, entry_price, stop_loss, target_price, risk_pct } = form
    if (!entry_price || !stop_loss || !target_price) return
    onSubmit({
      capital:      parseFloat(capital),
      entry_price:  parseFloat(entry_price),
      stop_loss:    parseFloat(stop_loss),
      target_price: parseFloat(target_price),
      risk_pct:     parseFloat(risk_pct),
    })
  }

  return (
    <div>
      <InputField
        label="Capital (₹)"
        value={form.capital}
        onChange={set('capital')}
        hint="Your total trading capital"
      />
      <InputField
        label="Entry price (₹)"
        value={form.entry_price}
        onChange={set('entry_price')}
        hint="Price at which you plan to buy"
      />
      <InputField
        label="Stop loss (₹)"
        value={form.stop_loss}
        onChange={set('stop_loss')}
        hint="Price at which you exit if wrong"
      />
      <InputField
        label="Target price (₹)"
        value={form.target_price}
        onChange={set('target_price')}
        hint="Price at which you take profit"
      />

      <div style={{ marginBottom: '16px' }}>
        <label style={{
          display:      'block',
          fontSize:     '11px',
          color:        'var(--color-text-secondary)',
          marginBottom: '4px',
        }}>
          Risk per trade: {form.risk_pct}%
        </label>
        <input
          type="range"
          min="0.1"
          max="5"
          step="0.1"
          value={form.risk_pct}
          onChange={(e) => set('risk_pct')(e.target.value)}
          style={{ width: '100%' }}
        />
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          fontSize:       '10px',
          color:          'var(--color-text-tertiary)',
          marginTop:      '2px',
        }}>
          <span>0.1% (conservative)</span>
          <span>5% (aggressive)</span>
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={isLoading || !form.entry_price || !form.stop_loss || !form.target_price}
        style={{
          width:        '100%',
          padding:      '9px',
          fontSize:     '13px',
          fontWeight:   '500',
          border:       'none',
          borderRadius: 'var(--border-radius-md)',
          background:   isLoading ? 'var(--color-border-secondary)' : 'var(--color-text-primary)',
          color:        'var(--color-background-primary)',
          cursor:       isLoading ? 'wait' : 'pointer',
          transition:   'opacity 0.15s',
        }}
      >
        {isLoading ? 'Calculating...' : 'Calculate risk'}
      </button>
    </div>
  )
}