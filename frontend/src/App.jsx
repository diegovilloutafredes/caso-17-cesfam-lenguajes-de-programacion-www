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
            <Route path="/medico" element={<ProtectedRoute role="doctor"><PanelMedico /></ProtectedRoute>} />
            <Route path="/farmacia" element={<ProtectedRoute role="pharmacy_staff"><PanelFarmacia /></ProtectedRoute>} />
            <Route path="/recetas" element={<ProtectedRoute role="pharmacy_staff"><Recetas /></ProtectedRoute>} />
            <Route path="/buscar-paciente" element={<ProtectedRoute role="pharmacy_staff"><BuscarPaciente /></ProtectedRoute>} />
            <Route path="/gestion-stock" element={<ProtectedRoute role="pharmacy_staff"><GestionStock /></ProtectedRoute>} />
          </Route>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  )
}
