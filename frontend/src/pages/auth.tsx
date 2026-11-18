import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

type AuthTab = 'login' | 'register'

export function AuthPage() {
  const { login, register } = useAuth()

  const [tab, setTab] = useState<AuthTab>('login')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Login fields
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')

  // Register fields
  const [regName, setRegName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirm, setRegConfirm] = useState('')

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    if (isSubmitting) return
    setError(null)
    setIsSubmitting(true)
    try {
      await login({ email: loginEmail, password: loginPassword })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    if (isSubmitting) return
    setError(null)

    if (regPassword !== regConfirm) {
      setError('Passwords do not match.')
      return
    }
    if (regPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setIsSubmitting(true)
    try {
      await register({ name: regName, email: regEmail, password: regPassword })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  function switchTab(next: AuthTab) {
    setTab(next)
    setError(null)
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        {/* Brand */}
        <div className="auth-brand">
          <span className="auth-brand-mark" aria-hidden="true">sr</span>
          <span className="auth-brand-name">Self-RAG</span>
        </div>

        {/* Tabs */}
        <div className="auth-tabs" role="tablist" aria-label="Authentication">
          <button
            role="tab"
            aria-selected={tab === 'login'}
            className={`auth-tab${tab === 'login' ? ' auth-tab--active' : ''}`}
            onClick={() => switchTab('login')}
            type="button"
          >
            Sign in
          </button>
          <button
            role="tab"
            aria-selected={tab === 'register'}
            className={`auth-tab${tab === 'register' ? ' auth-tab--active' : ''}`}
            onClick={() => switchTab('register')}
            type="button"
          >
            Create account
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="auth-error" role="alert" aria-live="assertive">
            {error}
          </div>
        )}

        {/* Login Form */}
        {tab === 'login' && (
          <form
            className="auth-form"
            id="login-form"
            onSubmit={(e) => void handleLogin(e)}
            aria-label="Sign in form"
          >
            <div className="auth-field">
              <label htmlFor="login-email">Email</label>
              <input
                autoComplete="email"
                className="auth-input"
                disabled={isSubmitting}
                id="login-email"
                onChange={(e) => setLoginEmail(e.currentTarget.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={loginEmail}
              />
            </div>
            <div className="auth-field">
              <label htmlFor="login-password">Password</label>
              <input
                autoComplete="current-password"
                className="auth-input"
                disabled={isSubmitting}
                id="login-password"
                onChange={(e) => setLoginPassword(e.currentTarget.value)}
                placeholder="••••••••"
                required
                type="password"
                value={loginPassword}
              />
            </div>
            <button
              className="auth-submit"
              disabled={isSubmitting || !loginEmail || !loginPassword}
              type="submit"
            >
              {isSubmitting && <span className="btn-spinner" aria-hidden="true" />}
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        )}

        {/* Register Form */}
        {tab === 'register' && (
          <form
            className="auth-form"
            id="register-form"
            onSubmit={(e) => void handleRegister(e)}
            aria-label="Create account form"
          >
            <div className="auth-field">
              <label htmlFor="reg-name">Full name</label>
              <input
                autoComplete="name"
                className="auth-input"
                disabled={isSubmitting}
                id="reg-name"
                onChange={(e) => setRegName(e.currentTarget.value)}
                placeholder="Ada Lovelace"
                required
                type="text"
                value={regName}
              />
            </div>
            <div className="auth-field">
              <label htmlFor="reg-email">Email</label>
              <input
                autoComplete="email"
                className="auth-input"
                disabled={isSubmitting}
                id="reg-email"
                onChange={(e) => setRegEmail(e.currentTarget.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={regEmail}
              />
            </div>
            <div className="auth-field">
              <label htmlFor="reg-password">Password</label>
              <input
                autoComplete="new-password"
                className="auth-input"
                disabled={isSubmitting}
                id="reg-password"
                minLength={8}
                onChange={(e) => setRegPassword(e.currentTarget.value)}
                placeholder="Min. 8 characters"
                required
                type="password"
                value={regPassword}
              />
            </div>
            <div className="auth-field">
              <label htmlFor="reg-confirm">Confirm password</label>
              <input
                autoComplete="new-password"
                className="auth-input"
                disabled={isSubmitting}
                id="reg-confirm"
                onChange={(e) => setRegConfirm(e.currentTarget.value)}
                placeholder="••••••••"
                required
                type="password"
                value={regConfirm}
              />
            </div>
            <button
              className="auth-submit"
              disabled={
                isSubmitting ||
                !regName ||
                !regEmail ||
                !regPassword ||
                !regConfirm
              }
              type="submit"
            >
              {isSubmitting && <span className="btn-spinner" aria-hidden="true" />}
              {isSubmitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
