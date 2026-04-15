// src/App.jsx

import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  BarChart2, TrendingUp, Brain, Shield,
  FlaskConical, Newspaper, Building2, Activity,
} from 'lucide-react'

import Dashboard  from './pages/Dashboard'
import Indicators from './pages/Indicators'
import Predict    from './pages/Predict'
import Risk       from './pages/Risk'
import Backtest   from './pages/Backtest'
import News       from './pages/News'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry:              2,
      refetchOnWindowFocus: false,
    },
  },
})

const NAV_ITEMS = [
  { to: '/',           icon: BarChart2,   label: 'Dashboard' },
  { to: '/indicators', icon: TrendingUp,  label: 'Indicators' },
  { to: '/predict',    icon: Brain,       label: 'Predict' },
  { to: '/risk',       icon: Shield,      label: 'Risk' },
  { to: '/backtest',   icon: FlaskConical, label: 'Backtest' },
  { to: '/news',       icon: Newspaper,   label: 'News' },
]

const navStyle = (isActive) => ({
  display:        'flex',
  alignItems:     'center',
  gap:            '8px',
  padding:        '8px 12px',
  borderRadius:   'var(--border-radius-md)',
  fontSize:       '13px',
  fontWeight:     '500',
  textDecoration: 'none',
  color:          isActive
    ? 'var(--color-text-primary)'
    : 'var(--color-text-secondary)',
  background: isActive
    ? 'var(--color-background-secondary)'
    : 'transparent',
  transition: 'background 0.15s, color 0.15s',
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div style={{ display: 'flex', minHeight: '100vh' }}>

          {/* Sidebar */}
          <aside style={{
            width:          '200px',
            flexShrink:     0,
            borderRight:    '0.5px solid var(--color-border-tertiary)',
            padding:        '1.5rem 1rem',
            display:        'flex',
            flexDirection:  'column',
            gap:            '4px',
            background:     'var(--color-background-primary)',
            position:       'sticky',
            top:            0,
            height:         '100vh',
            overflowY:      'auto',
          }}>
            {/* Logo */}
            <div style={{ marginBottom: '1.5rem' }}>
              <p style={{
                fontSize:   '15px',
                fontWeight: '500',
                color:      'var(--color-text-primary)',
                margin:     0,
              }}>
                TradeHelp
              </p>
              <p style={{
                fontSize: '11px',
                color:    'var(--color-text-tertiary)',
                margin:   '2px 0 0',
              }}>
                Indian Markets Analytics
              </p>
            </div>

            {/* Nav links */}
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                style={({ isActive }) => navStyle(isActive)}
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </aside>

          {/* Main content */}
          <main style={{
            flex:       1,
            padding:    '1.5rem',
            minWidth:   0,
            background: 'var(--color-background-tertiary)',
          }}>
            <Routes>
              <Route path="/"           element={<Dashboard />} />
              <Route path="/indicators" element={<Indicators />} />
              <Route path="/predict"    element={<Predict />} />
              <Route path="/risk"       element={<Risk />} />
              <Route path="/backtest"   element={<Backtest />} />
              <Route path="/news"       element={<News />} />
            </Routes>
          </main>

        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}