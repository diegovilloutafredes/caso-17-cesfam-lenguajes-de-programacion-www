import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardsApi, notificationsApi, patientsApi, prescriptionsApi } from '../api'
import Modal from '../components/Modal'
import { Bar, Doughnut, ChartCard, CHART, baseOptions } from '../components/charts'
import { Badge, Kpi, PageHeader, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { prescriptionStatus, stockStatus, fullName } from '../lib/format'
import { allowedActions } from '../lib/prescriptionActions'

const EVENT_LABELS = {
  RESERVATION_AVAILABLE: 'Disponible para retiro',
  PICKUP_REMINDER: 'Recordatorio de retiro',
}

const TOP_WINDOWS = [
  { days: 30, label: 'Últimos 30 días' },
  { days: 90, label: 'Últimos 90 días' },
  { days: 365, label: 'Último año' },
  { days: 0, label: 'Todo el histórico' },
]

export default function PanelFarmacia() {
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [topMeds, setTopMeds] = useState([])
  const [topDays, setTopDays] = useState(90)
  const topDaysRef = useRef(90) // ventana vigente para los refrescos de load()
  const topReqRef = useRef(0)
  const loadReqRef = useRef(0)
  const [busyId, setBusyId] = useState(null)

  // La cola solo trae patientId; los nombres salen de este catálogo.
  const [patientsById, setPatientsById] = useState({})

  // modal Avisos enviados
  const [avisosOpen, setAvisosOpen] = useState(false)
  const [avisos, setAvisos] = useState([])
  const [avisosLoading, setAvisosLoading] = useState(false)

  // modal Sin stock
  const [stockRx, setStockRx] = useState(null)
  const [stockAction, setStockAction] = useState('reserve')
  const [externalNotes, setExternalNotes] = useState('')
  const [cancelReason, setCancelReason] = useState('')
  const [stockSubmitting, setStockSubmitting] = useState(false)

  async function fetchTop(days) {
    const req = ++topReqRef.current
    try {
      const res = await dashboardsApi.pharmacyTopMedications(days)
      if (topReqRef.current === req) setTopMeds(res.topMedications || [])
    } catch (err) {
      if (topReqRef.current === req) showToast('Error al cargar el top', err.message, 'danger')
    }
  }

  async function load() {
    const req = ++loadReqRef.current
    setLoading(true)
    try {
      const d = await dashboardsApi.pharmacy()
      if (loadReqRef.current !== req) return
      setData(d)
      if (topDaysRef.current === 90) setTopMeds(d.topMedications || [])
      else fetchTop(topDaysRef.current)
    } catch (err) {
      if (loadReqRef.current !== req) return
      showToast('Error al cargar el panel', err.message, 'danger')
    } finally {
      if (loadReqRef.current === req) setLoading(false)
    }
  }

  function changeTopWindow(days) {
    topDaysRef.current = days
    setTopDays(days)
    fetchTop(days)
  }

  useEffect(() => {
    load()
    let active = true
    patientsApi
      .list({ page: 1, limit: 100 })
      .then((res) => {
        if (active) setPatientsById(Object.fromEntries((res.data || []).map((p) => [p.id, p])))
      })
      .catch(() => {
        /* sin catálogo la cola muestra el id */
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function patientLabel(rx) {
    const p = patientsById[rx.patientId]
    return p ? fullName(p) : rx.patientId
  }

  async function openAvisos() {
    setAvisosOpen(true)
    setAvisosLoading(true)
    try {
      const res = await notificationsApi.list()
      setAvisos(res || [])
    } catch (err) {
      showToast('Error al cargar los avisos', err.message, 'danger')
    } finally {
      setAvisosLoading(false)
    }
  }

  async function handleMarkAvailable(rx) {
    setBusyId(rx.id)
    try {
      await prescriptionsApi.markAvailable(rx.id)
      showToast('Marcada disponible', `Receta ${rx.id} lista para retiro.`, 'success')
      await load()
    } catch (err) {
      showToast('No se pudo marcar disponible', err.message, 'danger')
    } finally {
      setBusyId(null)
    }
  }

  async function handlePrepare(rx) {
    setBusyId(rx.id)
    try {
      await prescriptionsApi.prepare(rx.id)
      showToast('Receta preparada', `Receta ${rx.id} lista.`, 'success')
      await load()
    } catch (err) {
      if (err.code === 'INSUFFICIENT_STOCK') {
        setStockRx(rx)
        setStockAction('reserve')
        setExternalNotes('')
        setCancelReason('')
      } else {
        showToast('No se pudo preparar', err.message, 'danger')
      }
    } finally {
      setBusyId(null)
    }
  }

  async function submitStockAction() {
    if (!stockRx) return
    if (stockAction === 'cancel' && !cancelReason.trim()) {
      showToast('Falta el motivo', 'Indica el motivo de la anulación.', 'warning')
      return
    }
    setStockSubmitting(true)
    try {
      if (stockAction === 'reserve') {
        await prescriptionsApi.reserve(stockRx.id)
        showToast('Receta reservada', `Receta ${stockRx.id} reservada.`, 'success')
      } else if (stockAction === 'external') {
        await prescriptionsApi.externalPurchase(stockRx.id, { notes: externalNotes })
        showToast('Compra externa registrada', `Receta ${stockRx.id}.`, 'success')
      } else {
        await prescriptionsApi.cancel(stockRx.id, { reason: cancelReason })
        showToast('Receta anulada', `Receta ${stockRx.id} anulada.`, 'warning')
      }
      setStockRx(null)
      await load()
    } catch (err) {
      showToast('No se pudo completar la acción', err.message, 'danger')
    } finally {
      setStockSubmitting(false)
    }
  }

  const kpis = data?.kpis || {}
  const queue = data?.queue || []
  const stockAlerts = data?.stockAlerts || []
  const stockSummary = data?.stockSummary
  const stockTop = data?.stockTop || []

  const topData = topMeds.length > 0 && {
    labels: topMeds.map((m) => m.description),
    datasets: [{ label: 'Unidades recetadas', data: topMeds.map((m) => m.quantity), backgroundColor: CHART.primary }],
  }
  const horizontalOptions = { ...baseOptions, indexAxis: 'y', plugins: { legend: { display: false } } }

  const distribData = stockSummary && {
    labels: ['Disponibles', 'Stock bajo', 'Sin stock'],
    datasets: [{ data: [stockSummary.available, stockSummary.lowStock, stockSummary.outOfStock], backgroundColor: [CHART.success, CHART.warning, CHART.danger] }],
  }
  const stockByMedData = stockTop.length > 0 && {
    labels: stockTop.map((m) => m.description),
    datasets: [{ label: 'Disponibles', data: stockTop.map((m) => m.available), backgroundColor: CHART.accent }],
  }

  return (
    <>
      <PageHeader title="Panel Farmacia" subtitle="Gestión de recetas y stock de medicamentos">
        <div className="row">
          <button className="btn btn-outline btn-sm" onClick={openAvisos}>Avisos enviados</button>
          <button className="btn btn-primary" onClick={() => navigate('/gestion-stock')}>
            ＋ Ingresar Stock
          </button>
        </div>
      </PageHeader>

      {loading ? (
        <div className="card">
          <p className="text-soft">Cargando…</p>
        </div>
      ) : (
        <>
          <section className="grid grid-3 mb-4">
            <Kpi
              type="info"
              icon="📋"
              num={kpis.pendingPrescriptions ?? 0}
              label="Recetas pendientes"
            />
            <Kpi
              type="warning"
              icon="⏱"
              num={kpis.activeReservations ?? 0}
              label="Reservas activas"
            />
            <Kpi
              type="success"
              icon="✅"
              num={kpis.readyForPickup ?? 0}
              label="Listas para retiro"
            />
          </section>

          {/* Reportería de inventario y demanda */}
          <section className="grid grid-3 mb-4">
            <ChartCard
              title="Top medicamentos recetados"
              subtitle={TOP_WINDOWS.find((w) => w.days === topDays)?.label || 'Demanda reciente'}
              actions={
                <select
                  className="select"
                  style={{ width: 'auto' }}
                  aria-label="Ventana de tiempo del top"
                  value={topDays}
                  onChange={(e) => changeTopWindow(Number(e.target.value))}
                >
                  {TOP_WINDOWS.map((w) => (
                    <option key={w.days} value={w.days}>{w.label}</option>
                  ))}
                </select>
              }
            >
              {topData ? <Bar data={topData} options={horizontalOptions} /> : <Empty>Sin datos.</Empty>}
            </ChartCard>
            <ChartCard title="Distribución de stock" subtitle="Salud del inventario">
              {distribData ? <Doughnut data={distribData} options={baseOptions} /> : <Empty>Sin datos de stock.</Empty>}
            </ChartCard>
            <ChartCard title="Stock por medicamento" subtitle="Unidades disponibles">
              {stockByMedData ? <Bar data={stockByMedData} options={baseOptions} /> : <Empty>Sin medicamentos.</Empty>}
            </ChartCard>
          </section>

          <div className="card mb-4">
            <h2 className="mt-0">Alertas de Stock</h2>
            {stockAlerts.length === 0 ? (
              <Empty>Sin alertas de stock.</Empty>
            ) : (
              stockAlerts.map((m) => {
                const st = stockStatus(m.status)
                return (
                  <div className="list-card" key={m.id}>
                    <div className="meta">
                      <strong>{m.description}</strong>
                      <small>
                        Stock: {m.stock?.availableQuantity ?? 0} / Mínimo: {m.minStock ?? 0}
                      </small>
                    </div>
                    <Badge type={st.badge}>{st.label}</Badge>
                  </div>
                )
              })
            )}
          </div>

          <div className="card">
            <h2 className="mt-0 mb-3">Cola de Recetas</h2>
            {queue.length === 0 ? (
              <Empty>No hay recetas en cola.</Empty>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Paciente</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.map((rx) => {
                    const st = prescriptionStatus(rx.status)
                    const acts = allowedActions(rx.status)
                    const busy = busyId === rx.id
                    return (
                      <tr key={rx.id}>
                        <td>
                          <strong>{rx.id}</strong>
                        </td>
                        <td>{patientLabel(rx)}</td>
                        <td>
                          <Badge type={st.badge}>{st.label}</Badge>
                        </td>
                        <td className="actions">
                          {acts.includes('prepare') && (
                            <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => handlePrepare(rx)}>
                              Preparar
                            </button>
                          )}
                          {acts.includes('markAvailable') && (
                            <button className="btn btn-success btn-sm" disabled={busy} onClick={() => handleMarkAvailable(rx)}>
                              Marcar disponible
                            </button>
                          )}
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

      {/* Modal: avisos enviados a pacientes y apoderados */}
      <Modal
        open={avisosOpen}
        onClose={() => setAvisosOpen(false)}
        large
        title="Avisos enviados"
        subtitle="Correos y mensajes de texto emitidos a pacientes y apoderados."
        actions={
          <button className="btn btn-outline" onClick={() => setAvisosOpen(false)}>Cerrar</button>
        }
      >
        {avisosLoading ? (
          <Empty>Cargando avisos…</Empty>
        ) : avisos.length === 0 ? (
          <Empty>Sin avisos registrados.</Empty>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Evento</th>
                <th>Canal</th>
                <th>Destinatario</th>
                <th>Receta</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {avisos.map((n) => {
                const patient = patientsById[n.recipientPatientId]
                const who = patient ? fullName(patient) : n.recipientPatientId || '—'
                return (
                  <tr key={n.id}>
                    <td>{n.sentAt ? n.sentAt.slice(0, 16).replace('T', ' ') : '—'}</td>
                    <td>{EVENT_LABELS[n.event] || n.event}</td>
                    <td>{n.type === 'EMAIL' ? 'Correo' : 'SMS'}</td>
                    <td>
                      {who}
                      {n.recipientGuardianId && <> <Badge type="muted">apoderado</Badge></>}
                      <br />
                      <small>{n.recipientAddress}</small>
                    </td>
                    <td>{n.prescriptionId || '—'}</td>
                    <td>
                      <Badge type={n.status === 'SENT' ? 'success' : n.status === 'ERROR' ? 'danger' : 'warning'}>
                        {n.status === 'SENT' ? 'Enviado' : n.status === 'ERROR' ? 'Error' : 'Pendiente'}
                      </Badge>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </Modal>

      {/* Modal: sin stock al preparar */}
      <Modal
        open={!!stockRx}
        onClose={() => setStockRx(null)}
        title="Sin stock"
        subtitle={stockRx ? `No hay existencias para preparar la receta ${stockRx.id}.` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setStockRx(null)} disabled={stockSubmitting}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={submitStockAction} disabled={stockSubmitting}>
              {stockSubmitting ? 'Procesando…' : 'Confirmar'}
            </button>
          </>
        }
      >
        <div className="radio-list">
          <label className="radio-row">
            <input
              type="radio"
              name="stockAction"
              checked={stockAction === 'reserve'}
              onChange={() => setStockAction('reserve')}
            />
            <span>Reservar receta</span>
          </label>
          <label className="radio-row">
            <input
              type="radio"
              name="stockAction"
              checked={stockAction === 'external'}
              onChange={() => setStockAction('external')}
            />
            <span>Compra externa</span>
          </label>
          <label className="radio-row">
            <input
              type="radio"
              name="stockAction"
              checked={stockAction === 'cancel'}
              onChange={() => setStockAction('cancel')}
            />
            <span>Anular receta</span>
          </label>
        </div>

        {stockAction === 'external' && (
          <div className="input-group" style={{ marginTop: 12 }}>
            <label htmlFor="externalNotes">Notas de compra externa</label>
            <input
              id="externalNotes"
              className="input"
              value={externalNotes}
              onChange={(e) => setExternalNotes(e.target.value)}
              placeholder="Detalle de la compra externa"
            />
          </div>
        )}

        {stockAction === 'cancel' && (
          <div className="input-group" style={{ marginTop: 12 }}>
            <label htmlFor="cancelReason">Motivo de anulación</label>
            <input
              id="cancelReason"
              className="input"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Motivo de la anulación"
            />
          </div>
        )}
      </Modal>
    </>
  )
}
