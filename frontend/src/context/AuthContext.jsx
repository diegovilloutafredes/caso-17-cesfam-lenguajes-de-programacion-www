import { createContext, useContext, useState, useCallback } from 'react'
import { authApi } from '../api'

const AuthContext = createContext(null)

function loadSession() {
  const token = localStorage.getItem('cesfam_token')
  const userRaw = localStorage.getItem('cesfam_user')
  if (!token || !userRaw) return { token: null, user: null }
  try {
    return { token, user: JSON.parse(userRaw) }
  } catch {
    return { token: null, user: null }
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadSession)

  const login = useCallback(async (username, password) => {
    const data = await authApi.login(username, password)
    localStorage.setItem('cesfam_token', data.token)
    localStorage.setItem('cesfam_user', JSON.stringify(data.user))
    setSession({ token: data.token, user: data.user })
    return data.user
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('cesfam_token')
    localStorage.removeItem('cesfam_user')
    setSession({ token: null, user: null })
  }, [])

  return (
    <AuthContext.Provider value={{ ...session, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
