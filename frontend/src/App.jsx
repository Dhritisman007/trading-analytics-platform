import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BarChart2, TrendingUp, Brain, Shield, FlaskConical, Newspaper } from 'lucide-react'

// Lazy load to catch import errors
const Dashboard = lazy(() => import('./pages/Dashboard').catch(e => {
  console.error('Dashboard error:', e)
  return { default: () => <div style={{ color: 'red', padding: '2rem' }}>Error loading Dashboard: {e.message}</div> }
}))
const Indicators = lazy(() => import('./pages/Indicators').catch(e => ({ default: () => <div style={{ color: 'red' }}>Error: {e.message}</div> })))
const Predict = lazy(() => import('./pages/Predict').catch(e => ({ default: () => <div style={{ color: 'red' }}>Error: {e.message}</div> })))
const Risk = lazy(() => import('./pages/Risk').catch(e => ({ default: () => <div style={{ color: 'red' }}>Error: {e.message}</div> })))
const Backtest = lazy(() => import('./pages/Backtest').catch(e => ({ default: () => <div style={{ color: 'red' }}>Error: {e.message}</div> })))
const News = lazy(() => import('./pages/News').catch(e => ({ default: () => <div style={{ color: 'red' }}>Error: {e.message}</div> })))

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

const NAV_ITEMS = [
  { to: '/', icon: BarChart2, label: 'Dashboard' },
  { to: '/indicators', icon: TrendingUp, label: 'Indicators' },
  { to: '/predict', icon: Brain, label: 'Predict' },
  { to: '/risk', icon: Shield, label: 'Risk' },
  { to: '/backtest', icon: FlaskConical, label: 'Backtest' },
  { to: '/news', icon: Newspaper, label: 'News' },
]

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div style={{ display: 'flex', minHeight: '100vh' }}>
          <aside style={{
            width: '200px',
            flexShrink: 0,
            borderRight: '0.5px solid var(--color-border-tertiary)',
            padding: '1.5rem 1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            background: 'var(--color-background-primary)',
            position: 'sticky',
            top: 0,
            height: '100vh',
            overflowY: 'auto',
          }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <p style={{ fontSize: '15px', fontWeight: '500', color: 'var(--color-text-primary)', margin: 0 }}>
                📈 TradeHelp
              </p>
              <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', margin: '2px 0 0' }}>
                Analytics Platform
              </p>
            </div>
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  borderRadius: 'var(--border-radius-md)',
                  fontSize: '13px',
                  fontWeight: '500',
                  textDecoration: 'none',
                  color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                  background: isActive ? 'var(--color-background-secondary)' : 'transparent',
                  transition: 'background 0.15s',
                })}
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </aside>
          <main style={{
            flex: 1,
            padding: '1.5rem',
            minWidth: 0,
            background: 'var(--color-background-tertiary)',
            overflowY: 'auto',
          }}>
            <Suspense fallback={<div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/indicators" element={<Indicators />} />
                <Route path="/predict" element={<Predict />} />
                <Route path="/risk" element={<Risk />} />
                <Route path="/backtest" element={<Backtest />} />
                <Route path="/news" element={<News />} />
              </Routes>
            </Suspense>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
