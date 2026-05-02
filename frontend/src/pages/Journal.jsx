// src/pages/Journal.jsx

import { useState }    from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client          from '../api/client'
import { formatPrice, formatPct, formatDate } from '../utils/formatters'
import { SYMBOLS }     from '../utils/constants'
import { Plus, X, Check } from 'lucide-react'

const SETUPS = ['Order Block', 'FVG', 'RSI Oversold', 'EMA Cross', 'MACD Signal', 'Supertrend', 'Breakout', 'Other']

const inputStyle = {
  width:        '100%',
  padding:      '7px 10px',
  fontSize:     '12px',
  border:       '0.5px solid var(--color-border-tertiary)',
  borderRadius: 'var(--border-radius-md)',
  background:   'var(--color-background-secondary)',
  color:        'var(--color-text-primary)',
  outline:      'none',
  boxSizing:    'border-box',
}

const labelStyle = {
  display:      'block',
  fontSize:     '10px',
  color:        'var(--color-text-secondary)',
  marginBottom: '3px',
}

export default function Journal() {
  const qc          = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [closingId, setClosingId] = useState(null)
  const [exitPrice, setExitPrice] = useState('')

  const [form, setForm] = useState({
    symbol:      '^NSEI',
    direction:   'LONG',
    entry_price: '',
    stop_loss:   '',
    target:      '',
    quantity:    '',
    setup:       '',
    notes:       '',
  })

  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }))

  const { data, isLoading } = useQuery({
    queryKey: ['journal'],
    queryFn:  () => client.get('/journal/'),
  })

  const addMutation = useMutation({
    mutationFn: (payload) => client.post('/journal/', payload),
    onSuccess:  () => {
      qc.invalidateQueries({ queryKey: ['journal'] })
      setShowForm(false)
      setForm({
        symbol: '^NSEI', direction: 'LONG',
        entry_price: '', stop_loss: '', target: '',
        quantity: '', setup: '', notes: '',
      })
    },
  })

  const closeMutation = useMutation({
    mutationFn: ({ id, exitPrice }) =>
      client.patch(`/journal/${id}/close`, { exit_price: parseFloat(exitPrice) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['journal'] })
      setClosingId(null)
      setExitPrice('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => client.delete(`/journal/${id}`),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['journal'] }),
  })

  const trades = data?.trades || []
  const stats  = data?.stats  || {}

  return (
    <div>
      {/* Header */}
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        marginBottom:   '1.25rem',
      }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '500', margin: '0 0 3px' }}>
            Trade Journal
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', margin: 0 }}>
            Log, track, and review every trade
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            display:      'flex',
            alignItems:   'center',
            gap:          '6px',
            padding:      '7px 14px',
            fontSize:     '12px',
            fontWeight:   '500',
            border:       'none',
            borderRadius: 'var(--border-radius-md)',
            background:   'var(--color-text-primary)',
            color:        'var(--color-background-primary)',
            cursor:       'pointer',
          }}
        >
          <Plus size={13} />
          Log trade
        </button>
      </div>

      {/* Stats row */}
      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
        gap:                 '8px',
        marginBottom:        '1.25rem',
      }}>
        {[
          { label: 'Total trades',  value: stats.total_trades || 0 },
          { label: 'Open trades',   value: stats.open_trades  || 0, color: '#BA7517' },
          { label: 'Win rate',      value: `${stats.win_rate_pct || 0}%`,
            color: parseFloat(stats.win_rate_pct) >= 50 ? '#1D9E75' : '#E24B4A' },
          { label: 'Winners',       value: stats.winners || 0, color: '#1D9E75' },
          { label: 'Losers',        value: stats.losers  || 0, color: '#E24B4A' },
          { label: 'Total P&L',
            value: stats.total_pnl ? `₹${stats.total_pnl}` : '—',
            color: parseFloat(stats.total_pnl) >= 0 ? '#1D9E75' : '#E24B4A' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background:   'var(--color-background-primary)',
            border:       '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-md)',
            padding:      '10px 12px',
          }}>
            <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '0 0 3px' }}>
              {label}
            </p>
            <p style={{
              fontSize:   '18px',
              fontWeight: '500',
              color:      color || 'var(--color-text-primary)',
              margin:     0,
            }}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* New trade form */}
      {showForm && (
        <div style={{
          background:   'var(--color-background-primary)',
          border:       '0.5px solid var(--color-border-tertiary)',
          borderRadius: 'var(--border-radius-lg)',
          padding:      '1rem 1.25rem',
          marginBottom: '12px',
        }}>
          <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 14px' }}>
            Log new trade
          </p>

          <div style={{
            display:             'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
            gap:                 '10px',
            marginBottom:        '10px',
          }}>
            <div>
              <label style={labelStyle}>Symbol</label>
              <select value={form.symbol} onChange={set('symbol')} style={inputStyle}>
                {SYMBOLS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Direction</label>
              <select value={form.direction} onChange={set('direction')} style={inputStyle}>
                <option value="LONG">LONG (Buy)</option>
                <option value="SHORT">SHORT (Sell)</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Entry price (₹)</label>
              <input type="number" value={form.entry_price} onChange={set('entry_price')} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Stop loss (₹)</label>
              <input type="number" value={form.stop_loss} onChange={set('stop_loss')} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Target (₹)</label>
              <input type="number" value={form.target} onChange={set('target')} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Quantity</label>
              <input type="number" value={form.quantity} onChange={set('quantity')} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Setup</label>
              <select value={form.setup} onChange={set('setup')} style={inputStyle}>
                <option value="">Select setup</option>
                {SETUPS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label style={labelStyle}>Notes</label>
            <textarea
              value={form.notes}
              onChange={set('notes')}
              rows={2}
              placeholder="Why did you take this trade?"
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => addMutation.mutate({
                ...form,
                entry_price: parseFloat(form.entry_price),
                stop_loss:   form.stop_loss ? parseFloat(form.stop_loss) : null,
                target:      form.target    ? parseFloat(form.target)    : null,
                quantity:    form.quantity  ? parseInt(form.quantity)    : null,
              })}
              disabled={!form.entry_price || addMutation.isPending}
              style={{
                padding:      '7px 16px',
                fontSize:     '12px',
                fontWeight:   '500',
                border:       'none',
                borderRadius: 'var(--border-radius-md)',
                background:   'var(--color-text-primary)',
                color:        'var(--color-background-primary)',
                cursor:       'pointer',
              }}
            >
              {addMutation.isPending ? 'Saving...' : 'Save trade'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              style={{
                padding:      '7px 14px',
                fontSize:     '12px',
                border:       '0.5px solid var(--color-border-tertiary)',
                borderRadius: 'var(--border-radius-md)',
                background:   'transparent',
                color:        'var(--color-text-secondary)',
                cursor:       'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Trade list */}
      {isLoading ? (
        <p style={{ color: 'var(--color-text-tertiary)', fontSize: '13px', textAlign: 'center', padding: '2rem' }}>
          Loading...
        </p>
      ) : trades.length === 0 ? (
        <div style={{
          textAlign:    'center',
          padding:      '3rem',
          background:   'var(--color-background-primary)',
          borderRadius: 'var(--border-radius-lg)',
          border:       '0.5px solid var(--color-border-tertiary)',
        }}>
          <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>
            No trades logged yet
          </p>
          <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', margin: 0 }}>
            Click "Log trade" to record your first trade
          </p>
        </div>
      ) : (
        trades.map((trade) => {
          const isLong    = trade.direction === 'LONG'
          const isOpen    = trade.status === 'open'
          const pnl       = trade.pnl
          const pnlColor  = pnl == null ? '#888780' : pnl >= 0 ? '#1D9E75' : '#E24B4A'

          return (
            <div key={trade.id} style={{
              background:   'var(--color-background-primary)',
              border:       '0.5px solid var(--color-border-tertiary)',
              borderRadius: 'var(--border-radius-lg)',
              padding:      '12px 14px',
              marginBottom: '8px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  {/* Direction badge */}
                  <span style={{
                    fontSize:     '11px',
                    fontWeight:   '500',
                    padding:      '2px 8px',
                    borderRadius: '20px',
                    background:   isLong ? '#E1F5EE' : '#FCEBEB',
                    color:        isLong ? '#085041' : '#791F1F',
                  }}>
                    {trade.direction}
                  </span>
                  <div>
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: '0 0 1px', color: 'var(--color-text-primary)' }}>
                      {trade.symbol}
                    </p>
                    <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: 0 }}>
                      {formatDate(trade.entry_date)} · {trade.setup || 'No setup tagged'}
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {/* P&L */}
                  {pnl != null && (
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ fontSize: '14px', fontWeight: '500', color: pnlColor, margin: 0 }}>
                        {pnl >= 0 ? '+' : ''}₹{formatPrice(pnl).replace('₹', '')}
                      </p>
                      <p style={{ fontSize: '10px', color: pnlColor, margin: 0 }}>
                        {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct}%
                      </p>
                    </div>
                  )}

                  {/* Status */}
                  <span style={{
                    fontSize:     '10px',
                    padding:      '2px 7px',
                    borderRadius: '20px',
                    background:   isOpen ? '#FAEEDA' : '#F1EFE8',
                    color:        isOpen ? '#633806' : '#888780',
                    fontWeight:   '500',
                  }}>
                    {trade.status}
                  </span>

                  {/* Close button */}
                  {isOpen && (
                    <button
                      onClick={() => setClosingId(closingId === trade.id ? null : trade.id)}
                      style={{
                        display:        'flex',
                        alignItems:     'center',
                        justifyContent: 'center',
                        width:          '22px',
                        height:         '22px',
                        borderRadius:   '50%',
                        border:         '0.5px solid var(--color-border-tertiary)',
                        background:     'transparent',
                        color:          '#1D9E75',
                        cursor:         'pointer',
                      }}
                    >
                      <Check size={11} />
                    </button>
                  )}

                  {/* Delete button */}
                  <button
                    onClick={() => deleteMutation.mutate(trade.id)}
                    style={{
                      display:        'flex',
                      alignItems:     'center',
                      justifyContent: 'center',
                      width:          '22px',
                      height:         '22px',
                      borderRadius:   '50%',
                      border:         '0.5px solid var(--color-border-tertiary)',
                      background:     'transparent',
                      color:          'var(--color-text-tertiary)',
                      cursor:         'pointer',
                    }}
                  >
                    <X size={11} />
                  </button>
                </div>
              </div>

              {/* Price levels */}
              <div style={{
                display:   'flex',
                gap:       '14px',
                marginTop: '8px',
                fontSize:  '11px',
                color:     'var(--color-text-secondary)',
              }}>
                <span>Entry: <strong>₹{trade.entry_price}</strong></span>
                {trade.stop_loss && <span>SL: <strong style={{ color: '#E24B4A' }}>₹{trade.stop_loss}</strong></span>}
                {trade.target    && <span>Target: <strong style={{ color: '#1D9E75' }}>₹{trade.target}</strong></span>}
                {trade.exit_price && <span>Exit: <strong>₹{trade.exit_price}</strong></span>}
                {trade.quantity  && <span>Qty: <strong>{trade.quantity}</strong></span>}
              </div>

              {/* Notes */}
              {trade.notes && (
                <p style={{
                  fontSize:   '11px',
                  color:      'var(--color-text-tertiary)',
                  margin:     '6px 0 0',
                  fontStyle:  'italic',
                }}>
                  "{trade.notes}"
                </p>
              )}

              {/* Close trade form */}
              {closingId === trade.id && (
                <div style={{
                  display:      'flex',
                  gap:          '8px',
                  marginTop:    '10px',
                  paddingTop:   '10px',
                  borderTop:    '0.5px solid var(--color-border-tertiary)',
                  alignItems:   'center',
                }}>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    Exit price:
                  </span>
                  <input
                    type="number"
                    value={exitPrice}
                    onChange={(e) => setExitPrice(e.target.value)}
                    placeholder="₹"
                    style={{ ...inputStyle, width: '120px', flex: 'none' }}
                  />
                  <button
                    onClick={() => closeMutation.mutate({ id: trade.id, exitPrice })}
                    disabled={!exitPrice || closeMutation.isPending}
                    style={{
                      padding:      '5px 12px',
                      fontSize:     '11px',
                      fontWeight:   '500',
                      border:       'none',
                      borderRadius: 'var(--border-radius-md)',
                      background:   '#1D9E75',
                      color:        '#fff',
                      cursor:       'pointer',
                    }}
                  >
                    Close trade
                  </button>
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}
