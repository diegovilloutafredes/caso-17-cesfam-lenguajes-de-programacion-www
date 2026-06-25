import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { initials } from '../lib/format'

const NAV = {
  doctor: [{ to: '/medico', icon: '🏠', label: 'Panel Médico' }],
  pharmacy_staff: [
    { to: '/farmacia', icon: '🏠', label: 'Panel Farmacia' },
    { to: '/recetas', icon: '📑', label: 'Recetas' },
    { to: '/buscar-paciente', icon: '🔎', label: 'Buscar Paciente' },
    { to: '/gestion-stock', icon: '📦', label: 'Gestión de Stock' },
  ],
}
const ROLE_LABEL = { doctor: 'Médico', pharmacy_staff: 'Funcionario de Farmacia' }

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const pills = NAV[user?.role] || []

  const onLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7V3z" />
            </svg>
          </div>
          <div className="brand-text">
            <strong>CESFAM</strong>
            <small>Sistema de Salud CESFAM<br />Centro de Atención Primaria</small>
          </div>
        </div>

        <div className="user-chip">
          <div className="avatar">{initials(user?.fullName)}</div>
          <div className="user-chip-text">
            <strong>{user?.fullName}</strong>
            <small>{ROLE_LABEL[user?.role] || user?.role}</small>
          </div>
        </div>

        {pills.map((p) => (
          <NavLink
            key={p.to}
            to={p.to}
            className={({ isActive }) => `nav-pill${isActive ? ' active' : ''}`}
          >
            <span className="icon">{p.icon}</span> {p.label}
          </NavLink>
        ))}

        <div className="sidebar-footer">
          <button className="logout-link" onClick={onLogout}>
            <span>🚪</span> Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
