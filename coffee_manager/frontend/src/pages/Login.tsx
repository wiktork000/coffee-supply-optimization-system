import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Text, TextInput, Button } from '@tremor/react'
import { api } from '../api/client'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.auth.login({ username, password })
      if (res.data.token) {
        localStorage.setItem('auth_token', res.data.token)
        api.setSecurityData(res.data.token)
      }
      localStorage.setItem('auth', 'true')
      navigate('/dashboard')
    } catch {
      setError('Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-tremor-background-muted dark:bg-dark-tremor-background flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <span className="text-5xl">☕</span>
          <h1 className="mt-3 text-2xl font-bold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            CoffeeOps
          </h1>
          <p className="text-sm text-tremor-content dark:text-dark-tremor-content mt-1">
            Coffee Supply Management System
          </p>
        </div>
        <Card>
          <p className="text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong mb-4">
            Sign in
          </p>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                Username
              </label>
              <TextInput
                placeholder="admin"
                value={username}
                onChange={e => setUsername(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                Password
              </label>
              <TextInput
                type="password"
                placeholder="••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </div>
            {error && <Text className="text-red-500 text-sm">{error}</Text>}
            <Button type="submit" loading={loading} className="w-full">
              Sign in
            </Button>
          </form>
        </Card>
        <div className="text-center mt-4">
          <a
            href="/distributor/login"
            className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle hover:text-tremor-content dark:hover:text-dark-tremor-content transition-colors"
          >
            Distributor portal →
          </a>
        </div>
      </div>
    </div>
  )
}
