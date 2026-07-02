import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { token, user: sessionUser, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (token) {
    return <Navigate to={sessionUser?.role === 'doctor' ? '/medico' : '/farmacia'} replace />
  }

  async function submit(e, presetUser) {
    if (e?.preventDefault) e.preventDefault()
    const u = presetUser || username
    if (!u) {
      setError('Ingresa tu usuario.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const user = await login(u, password || 'x')
      navigate(user.role === 'doctor' ? '/medico' : '/farmacia', { replace: true })
    } catch (err) {
      setError(err.message || 'No se pudo iniciar sesión.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="brand">
          <div className="brand-logo">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7V3z" />
            </svg>
          </div>
          <div className="brand-text">
            <strong>CESFAM</strong>
            <small>Sistema de Salud</small>
          </div>
        </div>

        <h1>Iniciar sesión</h1>
        <p className="subtitle">Sistema de Salud — Centro de Atención Primaria</p>

        <form onSubmit={submit}>
          <div className="input-group">
            <label htmlFor="user">Usuario</label>
            <input
              id="user"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="drperez / mgonzalez"
              autoComplete="username"
            />
          </div>
          <div className="input-group">
            <label htmlFor="pass">Contraseña</label>
            <input
              id="pass"
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Ingresa tu contraseña"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="text-soft" style={{ color: 'var(--danger-text)' }}>
              {error}
            </p>
          )}

          <div className="role-btns">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Ingresando…' : 'Ingresar'}
            </button>
          </div>
          <div className="role-btns">
            <button type="button" className="btn btn-outline" disabled={loading}
              onClick={(e) => submit(e, 'drperez')}>
              Ingresar como Médico
            </button>
            <button type="button" className="btn btn-outline" disabled={loading}
              onClick={(e) => submit(e, 'mgonzalez')}>
              Ingresar como Funcionario
            </button>
          </div>
        </form>

        <footer>© 2026 CESFAM — Sistema de Salud</footer>
      </section>
    </main>
  )
}
