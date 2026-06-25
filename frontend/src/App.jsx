import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './screens/Login'
import PanelMedico from './screens/PanelMedico'
import PanelFarmacia from './screens/PanelFarmacia'
import Recetas from './screens/Recetas'
import BuscarPaciente from './screens/BuscarPaciente'
import GestionStock from './screens/GestionStock'

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/medico" element={<PanelMedico />} />
            <Route path="/farmacia" element={<PanelFarmacia />} />
            <Route path="/recetas" element={<Recetas />} />
            <Route path="/buscar-paciente" element={<BuscarPaciente />} />
            <Route path="/gestion-stock" element={<GestionStock />} />
          </Route>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  )
}
