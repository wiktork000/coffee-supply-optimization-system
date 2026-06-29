import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Distributors from './pages/Distributors'
import Buildings from './pages/Buildings'
import Optimization from './pages/Optimization'
import Orders from './pages/Orders'
import DistributorLogin from './pages/DistributorLogin'
import DistributorPanel from './pages/DistributorPanel'

function RequireAuth({ children }: { children: React.ReactNode }) {
  return localStorage.getItem('auth') ? <>{children}</> : <Navigate to="/login" replace />
}

function RequireDistributorAuth({ children }: { children: React.ReactNode }) {
  return localStorage.getItem('dist_auth') ? <>{children}</> : <Navigate to="/distributor/login" replace />
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/distributor/login" element={<DistributorLogin />} />
          <Route
            path="/distributor"
            element={
              <RequireDistributorAuth>
                <DistributorPanel />
              </RequireDistributorAuth>
            }
          />
          <Route
            path="/*"
            element={
              <RequireAuth>
                <Layout>
                  <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/distributors" element={<Distributors />} />
                    <Route path="/buildings" element={<Buildings />} />
                    <Route path="/optimization" element={<Optimization />} />
                    <Route path="/orders" element={<Orders />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Layout>
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
