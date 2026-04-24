// src/App.jsx — complete final version

import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import {
  BarChart2, TrendingUp, Brain, Shield,
  FlaskConical, Newspaper, Building2,
  CandlestickChart, Activity,
} from 'lucide-react'

import Dashboard  from './pages/Dashboard'
import Indicators from './pages/Indicators'
import Predict    from './pages/Predict'
import Risk       from './pages/Risk'
import Backtest   from './pages/Backtest'
import News       from './pages/News'
import FiiDii     from './pages/FiiDii'
import SMC        from './pages/SMC'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry:               2,
      refetchOnWindowFocus: false,
    },
  },
})

const NAV_ITEMS = [
  { to: '/',           icon: BarChart2,       label: 'Dashboard'   },
  { to: '/indicators', icon: TrendingUp,      label: 'Indicators'  },
  { to: '/smc',        icon: CandlestickChart, label: 'SMC / FVG'  },
  { to: '/predict',    icon: Brain,           label: 'Predict'     },
  { to: '/risk',       icon: Shield,          label: 'Risk'        },
  { to: '/backtest',   icon: FlaskConical,    label: 'Backtest'    },
  { to: '/news',       icon: Newspaper,       label: 'News'        },
  { to: '/fii-dii',    icon: Building2,       label: 'FII / DII'   },
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
  transition: 'all 0.15s',
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div style={{ display: 'flex', minHeight: '100vh' }}>

          {/* Sidebar */}
          <aside style={{
            width:         '200px',
            flexShrink:    0,
            borderRight:   '0.5px solid var(--color-border-tertiary)',
            padding:       '1.5rem 1rem',
            display:       'flex',
            flexDirection: 'column',
            gap:           '2px',
            background:    'var(--color-background-primary)',
            position:      'sticky',
            top:           0,
            height:        '100vh',
            overflowY:     'auto',
          }}>

            {/* Logo */}
            <div style={{ marginBottom: '1.5rem', padding: '0 4px' }}>
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

            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                style={({ isActive }) => navStyle(isActive)}
              >
                <Icon size={15} strokeWidth={1.8} />
                {label}
              </NavLink>
            ))}

            {/* Bottom — backend status */}
            <div style={{
              marginTop:  'auto',
              paddingTop: '1rem',
              borderTop:  '0.5px solid var(--color-border-tertiary)',
            }}>
              <BackendStatus />
            </div>
          </aside>

          {/* Main content */}
          <main style={{
            flex:       1,
            padding:    '1.5rem',
            minWidth:   0,
            background: 'var(--color-background-tertiary)',
          }}>
            <Routes>
              <Route path="/"           element={<Dashboard />}  />
              <Route path="/indicators" element={<Indicators />} />
              <Route path="/smc"        element={<SMC />}        />
              <Route path="/predict"    element={<Predict />}    />
              <Route path="/risk"       element={<Risk />}       />
              <Route path="/backtest"   element={<Backtest />}   />
              <Route path="/news"       element={<News />}       />
              <Route path="/fii-dii"    element={<FiiDii />}     />
            </Routes>
          </main>

        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Small backend status indicator in sidebar footer
function BackendStatus() {
  const { data, isError } = useQuery({
    queryKey:        ['health'],
    queryFn:         () => fetch('/api/health').then((r) => r.json()),
    refetchInterval: 30000,
    retry:           false,
  })

  const isOk = !isError && data?.status === 'healthy'

  return (
    <div style={{
      display:    'flex',
      alignItems: 'center',
      gap:        '6px',
      fontSize:   '10px',
      color:      'var(--color-text-tertiary)',
    }}>
      <span style={{
        width:        '6px',
        height:       '6px',
        borderRadius: '50%',
        background:   isOk ? '#1D9E75' : '#E24B4A',
        display:      'inline-block',
      }} />
      {isOk ? 'API connected' : 'API offline'}
    </div>
  )
}