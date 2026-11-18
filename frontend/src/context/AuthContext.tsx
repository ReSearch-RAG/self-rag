import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { getMe, login as apiLogin, register as apiRegister } from '../services/api'
import type { LoginPayload, RegisterPayload, User } from '../types'

const TOKEN_KEY = 'self_rag_token'

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY),
  )
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On mount, try to restore session from stored token
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY)
    if (!stored) {
      setIsLoading(false)
      return
    }

    let active = true
    getMe(stored)
      .then((u) => {
        if (active) {
          setUser(u)
          setToken(stored)
        }
      })
      .catch(() => {
        if (active) {
          localStorage.removeItem(TOKEN_KEY)
          setToken(null)
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    const { access_token } = await apiLogin(payload)
    localStorage.setItem(TOKEN_KEY, access_token)
    setToken(access_token)
    const u = await getMe(access_token)
    setUser(u)
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    // Register creates the account; then auto-login
    await apiRegister(payload)
    await login({ email: payload.email, password: payload.password })
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return ctx
}
