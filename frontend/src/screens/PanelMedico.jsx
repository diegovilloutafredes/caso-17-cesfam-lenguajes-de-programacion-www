import { useState, useEffect, useCallback } from 'react'
import { dashboardsApi, patientsApi, inventoryApi, prescriptionsApi } from '../api'
import Modal from '../components/Modal'
import ActivePrescriptionsList from '../components/ActivePrescriptionsList'
import { Doughnut, ChartCard, CHART, baseOptions } from '../components/charts'
import { SearchBar, PageHeader, Empty, Badge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { prescriptionStatus, fullName, computeStockStatus } from '../lib/format'

const emptyForm = {
  patientId: '',
  medicationId: '',
  intervalHours: '8',
  durationDays: '7',
  treatmentType: 'SHORT',
  totalQuantity: '',
}

const STATE_COLORS = {
  SUBMITTED: CHART.primary,
  RESERVED: CHART.accent,
  READY_FOR_PICKUP: CHART.warning,
  PICKED_UP: CHART.success,
  EXTERNAL_PURCHASE: CHART.info,
  CANCELLED: CHART.danger,
  EXPIRED: '#9CA3AF',
}

function medStock(m) {
  const a = m?.stock?.availableQuantity ?? 0
  const status = computeStockStatus(m)
  if (status === 'OUT_OF_STOCK') return { label: 'Sin stock', type: 'danger' }
  if (status === 'LOW_STOCK') return { label: `Stock bajo (${a} disponibles)`, type: 'warning' }
  return { label: `En stock (${a} disponibles)`, type: 'success' }
}

export default function PanelMedico() {
  const { showToast } = useToast()

  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState('')
  const [results, setResults] = useState(null) // null = sin búsqueda activa

  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(false)

  const [rxOpen, setRxOpen] = useState(false)
  const [medications, setMedications] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    try {
      const doctor = await dashboardsApi.doctor()
      setDashboard(doctor)
    } catch (err) {
      showToast('Error al cargar el panel', err.message, 'danger')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  // sin texto muestra los recientes; con texto busca con debounce
  useEffect(() => {
    const term = search.trim()
    if (!term) {
      setResults(null)
      return
    }
    let cancelled = false
    const t = setTimeout(async () => {
      try {
        const res = await patientsApi.list({ search: term, page: 1, limit: 10 })
        if (!cancelled) setResults(res.data || [])
      } catch (err) {
        if (!cancelled) showToast('Error en la búsqueda', err.message, 'danger')
      }
    }, 300)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [search, showToast])

  const patients = results ?? (dashboard?.recentPatients || [])

  async function openHistory(patientId) {
    setHistoryOpen(true)
    setHistory(null)
    setHistoryLoading(true)
    try {
      const data = await patientsApi.history(patientId)
      setHistory(data)
    } catch (err) {
      showToast('Error al cargar la libreta', err.message, 'danger')
      setHistoryOpen(false)
    } finally {
      setHistoryLoading(false)
    }
  }

  async function openPrescription() {
    setForm(emptyForm)
    setRxOpen(true)
    if (medications.length === 0) {
      try {
        const res = await inventoryApi.listMedications({ page: 1, limit: 100 })
        setMedications(res.data || [])
      } catch (err) {
        showToast('Error al cargar medicamentos', err.message, 'danger')
      }
    }
  }

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function submitPrescription() {
    if (!form.patientId || !form.medicationId || !form.totalQuantity) {
      showToast('Datos incompletos', 'Selecciona paciente, medicamento y cantidad.', 'warning')
      return
    }
    setSaving(true)
    try {
      const intervalHours = Number(form.intervalHours)
      const durationDays = Number(form.durationDays)
      const deadline = new Date()
      deadline.setDate(deadline.getDate() + durationDays)
      const pickupDeadline = deadline.toISOString().slice(0, 10)

      await prescriptionsApi.create({
        patientId: form.patientId,
        treatmentType: form.treatmentType,
        durationDays,
        pickupDeadline,
        items: [
          {
            medicationId: form.medicationId,
            dosesPerInterval: 1,
            intervalHours,
            doseDescription: `1 dosis cada ${intervalHours}h`,
            durationDays,
            totalQuantity: Number(form.totalQuantity),
          },
        ],
      })
      showToast('Receta creada', 'Emitida y enviada a farmacia.', 'success')
      setRxOpen(false)
      loadDashboard()
    } catch (err) {
      showToast('Error al crear la receta', err.message, 'danger')
    } finally {
      setSaving(false)
    }
  }

  const states = dashboard?.prescriptionStates || []
  const stateData = states.length > 0 && {
    labels: states.map((s) => prescriptionStatus(s.status).label),
    datasets: [
      {
        data: states.map((s) => s.count),
        backgroundColor: states.map((s) => STATE_COLORS[s.status] || CHART.primary),
      },
    ],
  }

  const selectedMed = medications.find((m) => m.id === form.medicationId)

  return (
    <>
      <PageHeader title="Panel Médico" subtitle="Gestión de pacientes y prescripciones">
        <button className="btn btn-primary" onClick={openPrescription}>
          ＋ Nueva Receta
        </button>
      </PageHeader>

      {loading && (
        <div className="card">
          <Empty>Cargando panel…</Empty>
        </div>
      )}

      {!loading && (
        <>
          {/* Reportería clínica: estado de las recetas */}
          <section className="mb-4">
            <ChartCard title="Recetas por estado" subtitle="Panorama de las recetas del sistema">
              {stateData ? <Doughnut data={stateData} options={baseOptions} /> : <Empty>Sin recetas.</Empty>}
            </ChartCard>
          </section>

          {/* Pacientes recientes (por última receta emitida) */}
          <div className="card">
            <h2>Pacientes Recientes</h2>
            <SearchBar
              value={search}
              onChange={setSearch}
              placeholder="Buscar paciente por nombre o RUT..."
              style={{ marginBottom: 12 }}
            />
            {patients.length === 0 ? (
              <Empty>No hay pacientes para mostrar.</Empty>
            ) : (
              patients.map((p) => (
                <div className="list-card" key={p.id}>
                  <div className="meta">
                    <strong>{fullName(p)}</strong>
                    <small>RUT: {p.rut}</small>
                  </div>
                  <div className="row" style={{ gap: 6 }}>
                    <button className="btn btn-outline btn-sm" onClick={() => openHistory(p.id)}>
                      Ver Libreta
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Modal: Libreta del paciente */}
      <Modal
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        title="Libreta del Paciente"
        subtitle="Carnet, recetas activas e historial completo de medicamentos."
        large
        actions={
          <button className="btn btn-outline" onClick={() => setHistoryOpen(false)}>
            Cerrar
          </button>
        }
      >
        {historyLoading && <Empty>Cargando libreta…</Empty>}
        {!historyLoading && history && (
          <>
            <div className="grid grid-2">
              <div className="input-group">
                <label>Nombre completo</label>
                <input className="input" type="text" value={fullName(history.patient)} readOnly />
              </div>
              <div className="input-group">
                <label>RUT</label>
                <input className="input" type="text" value={history.patient?.rut || ''} readOnly />
              </div>
              <div className="input-group">
                <label>Fecha de nacimiento</label>
                <input className="input" type="text" value={history.patient?.birthDate || ''} readOnly />
              </div>
              <div className="input-group">
                <label>Carnet de Paciente</label>
                <input
                  className="input"
                  type="text"
                  value={history.patient?.patientCard?.number || ''}
                  readOnly
                />
              </div>
            </div>

            <ActivePrescriptionsList
              prescriptions={history.activePrescriptions}
              renderMeta={(rx) =>
                `${rx.items?.[0]?.doseDescription || '—'} · Retiro hasta ${rx.pickupDeadline}`
              }
            />

            <div className="modal-section">
              <h3>Historial completo</h3>
              {(history.fullHistory || []).length === 0 ? (
                <Empty>Sin historial.</Empty>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Fecha emisión</th>
                      <th>Dosis</th>
                      <th>Duración</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.fullHistory.map((rx) => {
                      const st = prescriptionStatus(rx.status)
                      const item = rx.items?.[0]
                      return (
                        <tr key={rx.id}>
                          <td>
                            <strong>{rx.id}</strong>
                          </td>
                          <td>{rx.emissionDate}</td>
                          <td>{item?.doseDescription || '—'}</td>
                          <td>{rx.durationDays} días</td>
                          <td>
                            <Badge type={st.badge}>{st.label}</Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </Modal>

      {/* Modal: Nueva receta */}
      <Modal
        open={rxOpen}
        onClose={() => setRxOpen(false)}
        title="Nueva Receta"
        subtitle="Completa los datos para emitir la receta del paciente."
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setRxOpen(false)} disabled={saving}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={submitPrescription} disabled={saving}>
              {saving ? 'Creando…' : 'Crear Receta'}
            </button>
          </>
        }
      >
        <div className="grid grid-2">
          <div className="input-group">
            <label htmlFor="rx-patient">Paciente</label>
            <select
              id="rx-patient"
              className="select"
              value={form.patientId}
              onChange={(e) => setField('patientId', e.target.value)}
            >
              <option value="">Seleccionar paciente</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {fullName(p)} — {p.rut}
                </option>
              ))}
            </select>
          </div>
          <div className="input-group">
            <label htmlFor="rx-medication">Medicamento</label>
            <select
              id="rx-medication"
              className="select"
              value={form.medicationId}
              onChange={(e) => setField('medicationId', e.target.value)}
            >
              <option value="">Seleccionar medicamento</option>
              {medications.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.description}
                </option>
              ))}
            </select>
            {selectedMed && (
              <div className="mt-2">
                <Badge type={medStock(selectedMed).type}>{medStock(selectedMed).label}</Badge>
              </div>
            )}
          </div>
          <div className="input-group">
            <label htmlFor="rx-interval">Frecuencia (horas)</label>
            <select
              id="rx-interval"
              className="select"
              value={form.intervalHours}
              onChange={(e) => setField('intervalHours', e.target.value)}
            >
              <option value="6">Cada 6 h</option>
              <option value="8">Cada 8 h</option>
              <option value="12">Cada 12 h</option>
              <option value="24">Cada 24 h</option>
            </select>
          </div>
          <div className="input-group">
            <label htmlFor="rx-duration">Duración (días)</label>
            <select
              id="rx-duration"
              className="select"
              value={form.durationDays}
              onChange={(e) => setField('durationDays', e.target.value)}
            >
              <option value="7">7 días</option>
              <option value="10">10 días</option>
              <option value="30">30 días</option>
            </select>
          </div>
          <div className="input-group">
            <label htmlFor="rx-treatment">Tipo de Tratamiento</label>
            <select
              id="rx-treatment"
              className="select"
              value={form.treatmentType}
              onChange={(e) => setField('treatmentType', e.target.value)}
            >
              <option value="SHORT">Corto</option>
              <option value="LONG">Largo</option>
            </select>
          </div>
          <div className="input-group">
            <label htmlFor="rx-quantity">Cantidad</label>
            <input
              id="rx-quantity"
              className="input"
              type="number"
              min="1"
              placeholder="Ej: 20"
              value={form.totalQuantity}
              onChange={(e) => setField('totalQuantity', e.target.value)}
            />
          </div>
        </div>
      </Modal>
    </>
  )
}
