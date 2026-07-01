import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardsApi, prescriptionsApi } from '../api'
import Modal from '../components/Modal'
import { Bar, Doughnut, ChartCard, CHART, baseOptions } from '../components/charts'
import { Badge, Kpi, PageHeader, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { prescriptionStatus, stockStatus } from '../lib/format'
import { allowedActions } from '../lib/prescriptionActions'

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

  // Modal "Sin stock" (al preparar una prescripción sin existencias).
  const [stockRx, setStockRx] = useState(null)
  const [stockAction, setStockAction] = useState('reserve')
  const [externalNotes, setExternalNotes] = useState('')
  const [cancelReason, setCancelReason] = useState('')
  const [stockSubmitting, setStockSubmitting] = useState(false)

  // Modal "Confirmar retiro" (al entregar una prescripción disponible).
  const [deliverRx, setDeliverRx] = useState(null)
  const [pickerType, setPickerType] = useState('patient')
  const [guardianId, setGuardianId] = useState('')
  const [thirdPartyRut, setThirdPartyRut] = useState('')
  const [thirdPartyName, setThirdPartyName] = useState('')
  const [batchId, setBatchId] = useState('')
  const [quantity, setQuantity] = useState('')
  const [deliverSubmitting, setDeliverSubmitting] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const d = await dashboardsApi.pharmacy()
      setData(d)
      setTopMeds(d.topMedications || [])
      setTopDays(90)
    } catch (err) {
      showToast('Error al cargar el panel', err.message, 'danger')
    } finally {
      setLoading(false)
    }
  }

  async function changeTopWindow(days) {
    setTopDays(days)
    try {
      const res = await dashboardsApi.pharmacyTopMedications(days)
      setTopMeds(res.topMedications || [])
    } catch (err) {
      showToast('Error al cargar el top', err.message, 'danger')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handlePrepare(rx) {
    try {
      await prescriptionsApi.prepare(rx.id)
      showToast('Prescripción preparada', `Prescripción ${rx.id} lista.`, 'success')
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
    }
  }

  async function submitStockAction() {
    if (!stockRx) return
    setStockSubmitting(true)
    try {
      if (stockAction === 'reserve') {
        await prescriptionsApi.reserve(stockRx.id)
        showToast('Prescripción reservada', `Prescripción ${stockRx.id} reservada.`, 'success')
      } else if (stockAction === 'external') {
        await prescriptionsApi.externalPurchase(stockRx.id, { notes: externalNotes })
        showToast('Compra externa registrada', `Prescripción ${stockRx.id}.`, 'success')
      } else {
        await prescriptionsApi.cancel(stockRx.id, { reason: cancelReason })
        showToast('Prescripción anulada', `Prescripción ${stockRx.id} anulada.`, 'warning')
      }
      setStockRx(null)
      await load()
    } catch (err) {
      showToast('No se pudo completar la acción', err.message, 'danger')
    } finally {
      setStockSubmitting(false)
    }
  }

  function openDeliver(rx) {
    setDeliverRx(rx)
    setPickerType('patient')
    setGuardianId('')
    setThirdPartyRut('')
    setThirdPartyName('')
    setBatchId('')
    setQuantity('')
  }

  async function submitDeliver() {
    if (!deliverRx) return
    if (!batchId || !(Number(quantity) > 0)) {
      showToast('Datos incompletos', 'Indica el lote y una cantidad válida.', 'warning')
      return
    }
    if (pickerType === 'guardian' && !guardianId) {
      showToast('Datos incompletos', 'Selecciona el apoderado que retira.', 'warning')
      return
    }
    if (pickerType === 'third_party' && (!thirdPartyRut || !thirdPartyName)) {
      showToast('Datos incompletos', 'Indica el RUT y el nombre del tercero autorizado.', 'warning')
      return
    }
    setDeliverSubmitting(true)
    try {
      const body = {
        pickerType,
        batches: [{ batchId, quantity: Number(quantity) }],
      }
      if (pickerType === 'guardian') body.guardianId = guardianId
      if (pickerType === 'third_party') {
        body.thirdPartyRut = thirdPartyRut
        body.thirdPartyName = thirdPartyName
      }
      await prescriptionsApi.deliver(deliverRx.id, body)
      showToast('Entrega registrada', `Prescripción ${deliverRx.id} retirada.`, 'success')
      setDeliverRx(null)
      await load()
    } catch (err) {
      showToast('No se pudo registrar la entrega', err.message, 'danger')
    } finally {
      setDeliverSubmitting(false)
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
      <PageHeader title="Panel Farmacia" subtitle="Gestión de prescripciones y stock de medicamentos">
        <button className="btn btn-primary" onClick={() => navigate('/gestion-stock')}>
          ＋ Ingresar Stock
        </button>
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
              label="Prescripciones pendientes"
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
            <h2 className="mt-0 mb-3">Cola de Prescripciones</h2>
            {queue.length === 0 ? (
              <Empty>No hay prescripciones en cola.</Empty>
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
                    return (
                      <tr key={rx.id}>
                        <td>
                          <strong>{rx.id}</strong>
                        </td>
                        <td>{rx.patientId}</td>
                        <td>
                          <Badge type={st.badge}>{st.label}</Badge>
                        </td>
                        <td className="actions">
                          {acts.includes('prepare') && (
                            <button className="btn btn-primary btn-sm" onClick={() => handlePrepare(rx)}>
                              Preparar
                            </button>
                          )}
                          {acts.includes('deliver') && (
                            <button className="btn btn-success btn-sm" onClick={() => openDeliver(rx)}>
                              Entregar
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

      {/* Modal: sin stock al preparar */}
      <Modal
        open={!!stockRx}
        onClose={() => setStockRx(null)}
        title="Sin stock"
        subtitle={stockRx ? `No hay existencias para preparar la prescripción ${stockRx.id}.` : ''}
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
        <div className="chips" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 8 }}>
          <label className="row">
            <input
              type="radio"
              name="stockAction"
              checked={stockAction === 'reserve'}
              onChange={() => setStockAction('reserve')}
            />
            <span>Reservar prescripción</span>
          </label>
          <label className="row">
            <input
              type="radio"
              name="stockAction"
              checked={stockAction === 'external'}
              onChange={() => setStockAction('external')}
            />
            <span>Compra externa</span>
          </label>
          <label className="row">
            <input
              type="radio"
              name="stockAction"
              checked={stockAction === 'cancel'}
              onChange={() => setStockAction('cancel')}
            />
            <span>Anular prescripción</span>
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
            <label htmlFor="cancelReason">Razón de anulación</label>
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

      {/* Modal: confirmar retiro */}
      <Modal
        open={!!deliverRx}
        onClose={() => setDeliverRx(null)}
        title="Confirmar retiro"
        subtitle={deliverRx ? `Entrega de la prescripción ${deliverRx.id}.` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setDeliverRx(null)} disabled={deliverSubmitting}>
              Cancelar
            </button>
            <button className="btn btn-success" onClick={submitDeliver} disabled={deliverSubmitting}>
              {deliverSubmitting ? 'Registrando…' : 'Confirmar entrega'}
            </button>
          </>
        }
      >
        <div className="chips" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 8 }}>
          <label className="row">
            <input
              type="radio"
              name="pickerType"
              checked={pickerType === 'patient'}
              onChange={() => setPickerType('patient')}
            />
            <span>Paciente</span>
          </label>
          <label className="row">
            <input
              type="radio"
              name="pickerType"
              checked={pickerType === 'guardian'}
              onChange={() => setPickerType('guardian')}
            />
            <span>Apoderado</span>
          </label>
          <label className="row">
            <input
              type="radio"
              name="pickerType"
              checked={pickerType === 'third_party'}
              onChange={() => setPickerType('third_party')}
            />
            <span>Tercero autorizado</span>
          </label>
        </div>

        {pickerType === 'guardian' && (
          <div className="input-group" style={{ marginTop: 12 }}>
            <label htmlFor="guardianId">ID del apoderado</label>
            <input
              id="guardianId"
              className="input"
              value={guardianId}
              onChange={(e) => setGuardianId(e.target.value)}
              placeholder="ID del apoderado"
            />
          </div>
        )}

        {pickerType === 'third_party' && (
          <>
            <div className="input-group" style={{ marginTop: 12 }}>
              <label htmlFor="thirdPartyRut">RUT del tercero</label>
              <input
                id="thirdPartyRut"
                className="input"
                value={thirdPartyRut}
                onChange={(e) => setThirdPartyRut(e.target.value)}
                placeholder="12.345.678-9"
              />
            </div>
            <div className="input-group">
              <label htmlFor="thirdPartyName">Nombre del tercero</label>
              <input
                id="thirdPartyName"
                className="input"
                value={thirdPartyName}
                onChange={(e) => setThirdPartyName(e.target.value)}
                placeholder="Nombre completo"
              />
            </div>
          </>
        )}

        <div className="grid grid-2" style={{ marginTop: 12 }}>
          <div className="input-group">
            <label htmlFor="batchId">ID de lote</label>
            <input
              id="batchId"
              className="input"
              value={batchId}
              onChange={(e) => setBatchId(e.target.value)}
              placeholder="ID del lote"
            />
          </div>
          <div className="input-group">
            <label htmlFor="quantity">Cantidad</label>
            <input
              id="quantity"
              className="input"
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="0"
            />
          </div>
        </div>
      </Modal>
    </>
  )
}
