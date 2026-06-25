import { useState, useEffect, useCallback } from 'react'
import { inventoryApi, reportsApi } from '../api'
import Modal from '../components/Modal'
import { Badge, Kpi, SearchBar, PageHeader, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { stockStatus } from '../lib/format'

// Calcula el estado de stock de un medicamento de la lista (no viene en el envelope).
function computeStatus(med) {
  const available = med.stock?.availableQuantity ?? 0
  if (available === 0) return 'OUT_OF_STOCK'
  if (available < (med.minStock ?? 0)) return 'LOW_STOCK'
  return 'AVAILABLE'
}

const REPORT_TYPES = [
  { value: 'STOCK', label: 'STOCK' },
  { value: 'RESERVED', label: 'Reservados' },
  { value: 'EXPIRED', label: 'Caducados' },
]

const WRITE_OFF_REASONS = [
  { value: 'EXPIRATION', label: 'Fecha de vencimiento' },
  { value: 'DAMAGED', label: 'Mal estado' },
  { value: 'BROKEN_PACKAGE', label: 'Envase roto' },
  { value: 'OTHER', label: 'Otro' },
]

export default function GestionStock() {
  const { showToast } = useToast()

  const [summary, setSummary] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [medications, setMedications] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  // Modales
  const [detail, setDetail] = useState(null) // medicamento con batches
  const [detailOpen, setDetailOpen] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [writeOffBatch, setWriteOffBatch] = useState(null) // batch sobre el que se da de baja
  const [reportOpen, setReportOpen] = useState(false)

  // Formularios
  const [addForm, setAddForm] = useState({ medicationId: '', batchNumber: '', initialQuantity: '', expirationDate: '' })
  const [writeOffForm, setWriteOffForm] = useState({ reason: '', quantity: '', discard: false, notes: '' })
  const [reportForm, setReportForm] = useState({ reportType: 'STOCK', dateFrom: '', dateTo: '' })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [sum, low, meds] = await Promise.all([
        inventoryApi.stockSummary(),
        inventoryApi.lowStock(),
        inventoryApi.listMedications({ search, page: 1, limit: 50 }),
      ])
      setSummary(sum)
      setAlerts(low || [])
      setMedications(meds.data || [])
    } catch (err) {
      showToast('Error al cargar', err.message, 'danger')
    } finally {
      setLoading(false)
    }
  }, [search, showToast])

  useEffect(() => {
    const t = setTimeout(() => load(), 300)
    return () => clearTimeout(t)
  }, [load])

  // Refresca todo lo dependiente tras una mutación; si el detalle está abierto, lo recarga.
  async function refresh(medId) {
    await load()
    if (medId) {
      try {
        const fresh = await inventoryApi.getMedication(medId)
        setDetail(fresh)
      } catch {
        /* el detalle puede haberse cerrado */
      }
    }
  }

  async function openDetail(med) {
    try {
      const full = await inventoryApi.getMedication(med.id)
      setDetail(full)
      setDetailOpen(true)
    } catch (err) {
      showToast('Error', err.message, 'danger')
    }
  }

  function openAdd(medId = '') {
    setAddForm({ medicationId: medId, batchNumber: '', initialQuantity: '', expirationDate: '' })
    setAddOpen(true)
  }

  function openWriteOff(batch) {
    setWriteOffForm({ reason: '', quantity: '', discard: false, notes: '' })
    setWriteOffBatch(batch)
  }

  async function submitAdd() {
    if (!addForm.medicationId || !addForm.batchNumber || !addForm.initialQuantity || !addForm.expirationDate) {
      showToast('Faltan datos', 'Completa todos los campos.', 'warning')
      return
    }
    try {
      await inventoryApi.addBatch(addForm.medicationId, {
        batchNumber: addForm.batchNumber,
        expirationDate: addForm.expirationDate,
        initialQuantity: Number(addForm.initialQuantity),
      })
      setAddOpen(false)
      showToast('Partida registrada', 'Stock actualizado.', 'success')
      await refresh(detailOpen ? addForm.medicationId : null)
    } catch (err) {
      showToast('Error al ingresar stock', err.message, 'danger')
    }
  }

  async function submitWriteOff() {
    if (!writeOffForm.reason || !writeOffForm.quantity) {
      showToast('Faltan datos', 'Indica motivo y cantidad.', 'warning')
      return
    }
    try {
      await inventoryApi.writeOff(writeOffBatch.id, {
        reason: writeOffForm.reason,
        quantity: Number(writeOffForm.quantity),
        discard: writeOffForm.discard,
        notes: writeOffForm.notes,
      })
      setWriteOffBatch(null)
      showToast('Baja registrada', 'Stock disponible descontado. Auditoría actualizada.', 'warning')
      await refresh(detail?.id)
    } catch (err) {
      showToast('Error al dar de baja', err.message, 'danger')
    }
  }

  async function downloadReport() {
    try {
      const csv = await reportsApi.generate(reportForm.reportType, reportForm.dateFrom || undefined, reportForm.dateTo || undefined)
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `informe-${reportForm.reportType.toLowerCase()}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      setReportOpen(false)
      showToast('Informe generado', 'El archivo .CSV se descargó.', 'success')
    } catch (err) {
      showToast('Error al generar informe', err.message, 'danger')
    }
  }

  return (
    <>
      <PageHeader title="Gestión de Stock" subtitle="Control de inventario de medicamentos">
        <div className="row">
          <button className="btn btn-outline btn-sm" onClick={() => setReportOpen(true)}>Generar informe .CSV</button>
          <button className="btn btn-primary" onClick={() => openAdd()}>＋ Ingresar Stock</button>
        </div>
      </PageHeader>

      {/* KPIs */}
      <section className="grid grid-4 mb-4">
        <Kpi icon="📦" num={summary?.totalMedications ?? 0} label="Total medicamentos" type="info" />
        <Kpi icon="✓" num={summary?.available ?? 0} label="Disponibles" type="success" />
        <Kpi icon="⚠" num={summary?.lowStock ?? 0} label="Stock bajo" type="warning" />
        <Kpi icon="⨯" num={summary?.outOfStock ?? 0} label="Sin stock" type="danger" />
      </section>

      {/* Alertas críticas */}
      <div className="card mb-4">
        <h2>⚠ Alertas Críticas de Stock ({alerts.length})</h2>
        {alerts.length === 0 ? (
          <Empty>No hay alertas de stock por el momento.</Empty>
        ) : (
          <div className="grid grid-2">
            {alerts.map((m) => {
              const s = stockStatus(m.status)
              return (
                <div className="list-card" key={m.id}>
                  <div className="meta">
                    <strong>{m.description}</strong>
                    <small>Stock: {m.stock?.availableQuantity ?? 0} unidades / Mínimo: {m.minStock}</small>
                  </div>
                  <Badge type={s.badge}>{s.label}</Badge>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Inventario */}
      <div className="card">
        <div className="row-between mb-3">
          <h2 className="mt-0">Inventario de Medicamentos</h2>
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Buscar medicamento, código o fabricante..."
          />
        </div>

        {loading ? (
          <Empty>Cargando inventario…</Empty>
        ) : medications.length === 0 ? (
          <Empty>No se encontraron medicamentos.</Empty>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Medicamento</th>
                <th>Stock Actual</th>
                <th>Stock Mínimo</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {medications.map((m) => {
                const s = stockStatus(computeStatus(m))
                return (
                  <tr key={m.id}>
                    <td>
                      <button className="link-btn" onClick={() => openDetail(m)}>
                        <strong>{m.description}</strong>
                      </button>
                      <br />
                      <small>{m.code}</small>
                    </td>
                    <td>{m.stock?.availableQuantity ?? 0} unidades</td>
                    <td>{m.minStock} unidades</td>
                    <td><Badge type={s.badge}>{s.label}</Badge></td>
                    <td className="actions">
                      <button className="btn btn-outline btn-sm" onClick={() => openDetail(m)}>Ver detalle</button>
                      <button className="btn btn-primary btn-sm" onClick={() => openAdd(m.id)}>Agregar Stock</button>
                      <button className="btn btn-outline btn-sm" onClick={() => openDetail(m)}>– Dar de baja</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal: Ver detalle */}
      <Modal
        open={detailOpen && !!detail}
        onClose={() => setDetailOpen(false)}
        large
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setDetailOpen(false)}>Cerrar</button>
            <button className="btn btn-primary" onClick={() => { setDetailOpen(false); openAdd(detail?.id) }}>
              ＋ Agregar partida
            </button>
          </>
        }
      >
        {detail && (() => {
          const s = stockStatus(computeStatus(detail))
          return (
            <>
              <div className="row-between" style={{ alignItems: 'flex-start' }}>
                <div>
                  <h2 style={{ margin: 0 }}>{detail.description}</h2>
                  <p className="modal-sub" style={{ margin: '4px 0 0' }}>Código {detail.code}</p>
                </div>
                <Badge type={s.badge}>{s.label}</Badge>
              </div>

              <div className="modal-section">
                <h3>Identificación del producto</h3>
                <div className="grid grid-2">
                  <div className="input-group"><label>Fabricante</label><input className="input" readOnly value={detail.manufacturer ?? ''} /></div>
                  <div className="input-group"><label>Tipo</label><input className="input" readOnly value={detail.type ?? ''} /></div>
                  <div className="input-group" style={{ gridColumn: 'span 2' }}><label>Componentes</label><input className="input" readOnly value={detail.components ?? ''} /></div>
                  <div className="input-group"><label>Contenido</label><input className="input" readOnly value={detail.content ?? ''} /></div>
                  <div className="input-group"><label>Gramaje</label><input className="input" readOnly value={detail.packaging ?? ''} /></div>
                  <div className="input-group"><label>Stock crítico</label><input className="input" readOnly value={`${detail.minStock ?? 0} unidades`} /></div>
                </div>
              </div>

              <div className="modal-section">
                <h3>Stock actual</h3>
                <div className="grid grid-3">
                  <Kpi icon="✓" num={detail.stock?.availableQuantity ?? 0} label="Disponible" type="success" />
                  <Kpi icon="⏱" num={detail.stock?.reservedQuantity ?? 0} label="Reservado" type="warning" />
                  <Kpi icon="📦" num={detail.stock?.physicalQuantity ?? 0} label="Físico" type="info" />
                </div>
              </div>

              <div className="modal-section">
                <h3>Partidas vigentes</h3>
                {!detail.batches || detail.batches.length === 0 ? (
                  <Empty>Sin partidas registradas.</Empty>
                ) : (
                  <table className="table">
                    <thead>
                      <tr><th>N° Partida</th><th>Ingreso</th><th>Vencimiento</th><th>Inicial</th><th>Disponible</th><th>Acción</th></tr>
                    </thead>
                    <tbody>
                      {detail.batches.map((b) => (
                        <tr key={b.id}>
                          <td><strong>{b.batchNumber}</strong></td>
                          <td>{b.arrivalDate}</td>
                          <td>{b.expirationDate}</td>
                          <td>{b.initialQuantity}</td>
                          <td>{b.availableQuantity}</td>
                          <td><button className="btn btn-outline btn-sm" onClick={() => openWriteOff(b)}>Baja</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )
        })()}
      </Modal>

      {/* Modal: Ingresar stock */}
      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Ingresar Stock"
        subtitle="Registrar una nueva partida de medicamentos."
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setAddOpen(false)}>Cancelar</button>
            <button className="btn btn-primary" onClick={submitAdd}>Guardar partida</button>
          </>
        }
      >
        <div className="grid grid-2">
          <div className="input-group">
            <label>Medicamento</label>
            <select
              className="select"
              value={addForm.medicationId}
              onChange={(e) => setAddForm({ ...addForm, medicationId: e.target.value })}
            >
              <option value="">Seleccionar medicamento</option>
              {medications.map((m) => (
                <option key={m.id} value={m.id}>{m.description}</option>
              ))}
            </select>
          </div>
          <div className="input-group">
            <label>N° Partida</label>
            <input
              className="input"
              type="text"
              placeholder="Ej: P-2026-001"
              value={addForm.batchNumber}
              onChange={(e) => setAddForm({ ...addForm, batchNumber: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label>Cantidad inicial</label>
            <input
              className="input"
              type="number"
              placeholder="Ej: 500"
              value={addForm.initialQuantity}
              onChange={(e) => setAddForm({ ...addForm, initialQuantity: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label>Fecha de vencimiento</label>
            <input
              className="input"
              type="date"
              value={addForm.expirationDate}
              onChange={(e) => setAddForm({ ...addForm, expirationDate: e.target.value })}
            />
          </div>
        </div>
      </Modal>

      {/* Modal: Dar de baja */}
      <Modal
        open={!!writeOffBatch}
        onClose={() => setWriteOffBatch(null)}
        title="Dar de baja medicamento"
        subtitle="Descontar del stock disponible. Si se desecha, también del stock físico."
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setWriteOffBatch(null)}>Cancelar</button>
            <button className="btn btn-danger" onClick={submitWriteOff}>Confirmar baja</button>
          </>
        }
      >
        {writeOffBatch && (
          <p className="modal-sub" style={{ marginTop: 0 }}>Partida <strong>{writeOffBatch.batchNumber}</strong></p>
        )}
        <div className="grid grid-2">
          <div className="input-group">
            <label>Motivo</label>
            <select
              className="select"
              value={writeOffForm.reason}
              onChange={(e) => setWriteOffForm({ ...writeOffForm, reason: e.target.value })}
            >
              <option value="">Seleccionar motivo</option>
              {WRITE_OFF_REASONS.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>
          <div className="input-group">
            <label>Cantidad</label>
            <input
              className="input"
              type="number"
              placeholder="Ej: 10"
              value={writeOffForm.quantity}
              onChange={(e) => setWriteOffForm({ ...writeOffForm, quantity: e.target.value })}
            />
          </div>
        </div>
        <div className="input-group mt-3 row" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            id="desechar"
            checked={writeOffForm.discard}
            onChange={(e) => setWriteOffForm({ ...writeOffForm, discard: e.target.checked })}
          />
          <label htmlFor="desechar" style={{ margin: 0 }}>Desechar físicamente (auditoría)</label>
        </div>
        <div className="input-group mt-3">
          <label>Observaciones</label>
          <textarea
            className="textarea"
            placeholder="Detalle del motivo..."
            value={writeOffForm.notes}
            onChange={(e) => setWriteOffForm({ ...writeOffForm, notes: e.target.value })}
          />
        </div>
      </Modal>

      {/* Modal: Generar informe CSV */}
      <Modal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        title="Generar informe (.CSV)"
        subtitle="Selecciona el tipo de informe a exportar."
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setReportOpen(false)}>Cancelar</button>
            <button className="btn btn-primary" onClick={downloadReport}>Descargar .CSV</button>
          </>
        }
      >
        <div className="input-group">
          <label>Tipo de informe</label>
          <select
            className="select"
            value={reportForm.reportType}
            onChange={(e) => setReportForm({ ...reportForm, reportType: e.target.value })}
          >
            {REPORT_TYPES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-2 mt-3">
          <div className="input-group">
            <label>Desde</label>
            <input
              className="input"
              type="date"
              value={reportForm.dateFrom}
              onChange={(e) => setReportForm({ ...reportForm, dateFrom: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label>Hasta</label>
            <input
              className="input"
              type="date"
              value={reportForm.dateTo}
              onChange={(e) => setReportForm({ ...reportForm, dateTo: e.target.value })}
            />
          </div>
        </div>
      </Modal>
    </>
  )
}
