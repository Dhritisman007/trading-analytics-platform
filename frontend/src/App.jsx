// src/App.jsx

import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Pages
import Dashboard  from './pages/Dashboard'
import Indicators from './pages/Indicators'
import SMC        from './pages/SMC'
import FiiDii     from './pages/FiiDii'
import News       from './pages/News'
import Predict    from './pages/Predict'
import Backtest   from './pages/Backtest'
import Risk       from './pages/Risk'

// ── QueryClient ───────────────────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry:              2,
      staleTime:          5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
})

// ── Navigation items ──────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { to: '/',           label: 'Dashboard',   icon: '📊' },
  { to: '/indicators', label: 'Indicators',  icon: '📈' },
  { to: '/smc',        label: 'SMC / FVG',   icon: '🎯' },
  { to: '/fii-dii',    label: 'FII / DII',   icon: '🏦' },
  { to: '/news',       label: 'News',        icon: '📰' },
  { to: '/predict',    label: 'AI Predict',  icon: '🤖' },
  { to: '/backtest',   label: 'Backtest',    icon: '🧪' },
  { to: '/risk',       label: 'Risk',        icon: '🛡️' },
]

// ── CSS design tokens ─────────────────────────────────────────────────────────
const TOKENS = `
  :root {
    --color-background-primary:   #FFFFFF;
    --color-background-secondary: #F8F7F4;
    --color-background-tertiary:  #F1EFE8;
    --color-text-primary:         #1A1916;
    --color-text-secondary:       #5F5E5A;
    --color-text-tertiary:        #888780;
    --color-border-primary:       #D3D1C7;
    --color-border-secondary:     #E2E0D8;
    --color-border-tertiary:      #EBEBEB;
    --color-accent:               #1D9E75;
    --color-accent-bg:            #E1F5EE;
    --color-danger:               #E24B4A;
    --color-warning:              #BA7517;
    --border-radius-sm:           4px;
    --border-radius-md:           6px;
    --border-radius-lg:           10px;
    --sidebar-width:              220px;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --color-background-primary:   #1C1C1A;
      --color-background-secondary: #242422;
      --color-background-tertiary:  #2C2C2A;
      --color-text-primary:         #EEEDE8;
      --color-text-secondary:       #9C9A92;
      --color-text-tertiary:        #6B6A65;
      --color-border-primary:       #444441;
      --color-border-secondary:     #363634;
      --color-border-tertiary:      #2C2C2A;
    }
  }
`

// ── Sidebar ───────────────────────────────────────────────────────────────────
function Sidebar({ collapsed, onToggle }) {
  return (
    <aside style={{
      width:            collapsed ? '56px' : 'var(--sidebar-width)',
      minHeight:        '100vh',
      background:       'var(--color-background-primary)',
      borderRight:      '0.5px solid var(--color-border-tertiary)',
      display:          'flex',
      flexDirection:    'column',
      position:         'sticky',
      top:              0,
      transition:       'width 0.2s ease',
      overflow:         'hidden',
      flexShrink:       0,
      zIndex:           10,
    }}>
      {/* Logo / brand */}
      <div style={{
        padding:      collapsed ? '18px 16px' : '18px 20px',
        borderBottom: '0.5px solid var(--color-border-tertiary)',
        display:      'flex',
        alignItems:   'center',
        gap:          '10px',
        cursor:       'pointer',
        userSelect:   'none',
      }} onClick={onToggle}>
        <span style={{ fontSize: '18px', flexShrink: 0 }}>📉</span>
        {!collapsed && (
          <div>
            <div style={{
              fontSize:   '13px',
              fontWeight: '600',
              color:      'var(--color-text-primary)',
              lineHeight: 1.2,
            }}>TradeHelp</div>
            <div style={{
              fontSize: '10px',
              color:    'var(--color-text-tertiary)',
            }}>Analytics Platform</div>
          </div>
        )}
      </div>

      {/* Nav links */}
      <nav style={{ padding: '10px 0', flex: 1 }}>
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display:      'flex',
              alignItems:   'center',
              gap:          '10px',
              padding:      collapsed ? '9px 16px' : '9px 20px',
              fontSize:     '13px',
              fontWeight:   isActive ? '500' : '400',
              color:        isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              background:   isActive ? 'var(--color-background-tertiary)' : 'transparent',
              borderLeft:   isActive ? '2px solid var(--color-accent)' : '2px solid transparent',
              textDecoration: 'none',
              whiteSpace:   'nowrap',
              overflow:     'hidden',
              transition:   'background 0.1s, color 0.1s',
            })}
          >
            <span style={{ fontSize: '15px', flexShrink: 0 }}>{icon}</span>
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div style={{
          padding:    '12px 20px',
          borderTop:  '0.5px solid var(--color-border-tertiary)',
          fontSize:   '10px',
          color:      'var(--color-text-tertiary)',
        }}>
          Indian Markets · NSE / BSE
        </div>
      )}
    </aside>
  )
}

// ── Main layout ───────────────────────────────────────────────────────────────
function Layout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--color-background-tertiary)' }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />

      <main style={{
        flex:       1,
        padding:    '24px',
        overflowX:  'hidden',
        minWidth:   0,
      }}>
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/indicators" element={<Indicators />} />
          <Route path="/smc"        element={<SMC />} />
          <Route path="/fii-dii"    element={<FiiDii />} />
          <Route path="/news"       element={<News />} />
          <Route path="/predict"    element={<Predict />} />
          <Route path="/backtest"   element={<Backtest />} />
          <Route path="/risk"       element={<Risk />} />
          {/* Catch-all → dashboard */}
          <Route path="*"           element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

// ── App root ──────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <>
      {/* Inject design tokens */}
      <style>{TOKENS}</style>

      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Layout />
        </BrowserRouter>
      </QueryClientProvider>
    </>
  )
}
