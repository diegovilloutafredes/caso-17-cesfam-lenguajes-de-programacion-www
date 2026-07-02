import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, role }) {
  const { token, user } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (role && user?.role !== role) {
    const home = user?.role === 'doctor' ? '/medico' : '/farmacia'
    return <Navigate to={home} replace />
  }
  return children
}
