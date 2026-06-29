import { NavLink, useNavigate } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/distributors', label: 'Distributors', icon: '📦' },
  { to: '/buildings', label: 'Buildings', icon: '🏢' },
  { to: '/optimization', label: 'Optimization', icon: '⚡' },
  { to: '/orders', label: 'Orders', icon: '📋' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()

  const handleLogout = () => {
    localStorage.removeItem('auth')
    localStorage.removeItem('auth_token')
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-tremor-background-muted dark:bg-dark-tremor-background">
      <aside className="w-56 bg-tremor-background dark:bg-dark-tremor-background-subtle border-r border-tremor-border dark:border-dark-tremor-border flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-tremor-border dark:border-dark-tremor-border">
          <span className="text-base font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            ☕ CoffeeOps
          </span>
          <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
            Supply Management
          </p>
        </div>

        <nav className="flex-1 px-3 py-3 space-y-0.5">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-tremor-small text-sm transition-colors ${
                  isActive
                    ? 'bg-tremor-brand-faint dark:bg-dark-tremor-brand-faint text-tremor-brand dark:text-dark-tremor-brand-emphasis font-medium'
                    : 'text-tremor-content dark:text-dark-tremor-content hover:bg-tremor-background-muted dark:hover:bg-dark-tremor-background hover:text-tremor-content-strong dark:hover:text-dark-tremor-content-strong'
                }`
              }
            >
              <span className="text-sm opacity-60">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-3 border-t border-tremor-border dark:border-dark-tremor-border space-y-3">
          <button
            onClick={toggle}
            className="w-full flex items-center gap-2 text-xs text-tremor-content dark:text-dark-tremor-content hover:text-tremor-content-strong dark:hover:text-dark-tremor-content-strong transition-colors"
          >
            <span className="text-base">{theme === 'dark' ? '☀️' : '🌙'}</span>
            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-full bg-tremor-brand flex items-center justify-center text-white text-xs font-bold shrink-0">
              C
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong truncate">
                Coordinator
              </p>
              <button
                onClick={handleLogout}
                className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle hover:text-red-500 transition-colors"
              >
                Logout →
              </button>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-7">
        {children}
      </main>
    </div>
  )
}
