import axios from 'axios'

// Una sola base URL: el ApiGateway (BFF). En local :8000, en cloud el desplegado.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

// Adjunta el token de sesión a cada request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cesfam_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Desenvuelve el envelope ApiResponse: en éxito devuelve `data`; en error normaliza
// el código/mensaje del backend a un Error. Respuestas no-envueltas (CSV) pasan crudas.
api.interceptors.response.use(
  (resp) => {
    const body = resp.data
    if (body && typeof body === 'object' && 'statusCode' in body && 'data' in body) {
      return body.data
    }
    return body
  },
  (error) => {
    const env = error.response?.data
    if (env && typeof env === 'object' && env.error) {
      const e = new Error(env.error.message || 'Error')
      e.code = env.error.code
      e.details = env.error.details
      e.status = error.response.status
      return Promise.reject(e)
    }
    return Promise.reject(error)
  },
)

export const authApi = {
  login: (username, password) => api.post('/api/v1/auth/login', { username, password }),
  me: () => api.get('/api/v1/auth/me'),
  logout: () => api.post('/api/v1/auth/logout'),
}

export const patientsApi = {
  list: (params) => api.get('/api/v1/patients', { params }),
  recent: (limit = 5) => api.get('/api/v1/patients/recent', { params: { limit } }),
  get: (id) => api.get(`/api/v1/patients/${id}`),
  update: (id, body) => api.put(`/api/v1/patients/${id}`, body),
  listGuardians: (id) => api.get(`/api/v1/patients/${id}/guardians`),
  addGuardian: (id, body) => api.post(`/api/v1/patients/${id}/guardians`, body),
  removeGuardian: (id, gid) => api.delete(`/api/v1/patients/${id}/guardians/${gid}`),
  history: (id) => api.get(`/api/v1/patients/${id}/history`),
}

export const inventoryApi = {
  listMedications: (params) => api.get('/api/v1/medications', { params }),
  getMedication: (id) => api.get(`/api/v1/medications/${id}`),
  stockSummary: () => api.get('/api/v1/medications/stock-summary'),
  lowStock: () => api.get('/api/v1/medications/low-stock'),
  listBatches: (id) => api.get(`/api/v1/medications/${id}/batches`),
  addBatch: (id, body) => api.post(`/api/v1/medications/${id}/batches`, body),
  writeOff: (batchId, body) => api.post(`/api/v1/batches/${batchId}/write-off`, body),
  listWriteOffs: (params) => api.get('/api/v1/write-offs', { params }),
}

export const prescriptionsApi = {
  list: (params) => api.get('/api/v1/prescriptions', { params }),
  queue: () => api.get('/api/v1/prescriptions/queue'),
  get: (id) => api.get(`/api/v1/prescriptions/${id}`),
  create: (body) => api.post('/api/v1/prescriptions', body),
  prepare: (id) => api.post(`/api/v1/prescriptions/${id}/prepare`),
  reserve: (id) => api.post(`/api/v1/prescriptions/${id}/reserve`),
  markAvailable: (id) => api.post(`/api/v1/prescriptions/${id}/mark-available`),
  externalPurchase: (id, body) => api.post(`/api/v1/prescriptions/${id}/external-purchase`, body),
  cancel: (id, body) => api.post(`/api/v1/prescriptions/${id}/cancel`, body),
  deliver: (id, body) => api.post(`/api/v1/prescriptions/${id}/deliver`, body),
}

export const notificationsApi = {
  list: (params) => api.get('/api/v1/notifications', { params }),
}

export const dashboardsApi = {
  doctor: () => api.get('/api/v1/doctor/dashboard'),
  pharmacy: () => api.get('/api/v1/pharmacy/dashboard'),
}

export const analyticsApi = {
  trend: (dateFrom, dateTo, eventType) =>
    api.get('/api/v1/analytics/prescription-trend', {
      params: { dateFrom, dateTo, ...(eventType ? { eventType } : {}) },
    }),
}

// Reportes devuelven CSV (texto plano), no envelope.
export const reportsApi = {
  generate: (reportType, dateFrom, dateTo) =>
    api.post('/api/v1/reports', { reportType, dateFrom, dateTo }, { responseType: 'text' }),
}

export default api
