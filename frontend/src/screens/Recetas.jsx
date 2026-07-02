import { useEffect, useMemo, useRef, useState } from 'react'
import { inventoryApi, patientsApi, prescriptionsApi } from '../api'
import DeliverModal from '../components/DeliverModal'
import Modal from '../components/Modal'
import { SearchBar, Badge, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { prescriptionStatus, fullName } from '../lib/format'
import { allowedActions } from '../lib/prescriptionActions'

const CHIPS = [
  { key: 'ALL', label: 'Todas', status: null },
  { key: 'SUBMITTED', label: 'Ingresado', status: 'SUBMITTED' },
  { key: 'READY_FOR_PICKUP', label: 'Disponibles', status: 'READY_FOR_PICKUP' },
  { key: 'RESERVED', label: 'Reservado', status: 'RESERVED' },
]

function totalQuantity(r) {
  if (!r.items?.length) return '—'
  return r.items.reduce((acc, it) => acc + (it.totalQuantity || 0), 0)
}

export default function Recetas() {
  const { showToast } = useToast()
  const [prescriptions, setPrescriptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [chip, setChip] = useState('ALL')
  const [search, setSearch] = useState('')

  const [busyId, setBusyId] = useState(null)
  const [pickup, setPickup] = useState(null)
  const [cancelRx, setCancelRx] = useState(null)
  const [cancelReason, setCancelReason] = useState('')

  // La receta solo trae ids; los nombres salen de estos catálogos.
  const [patientsById, setPatientsById] = useState({})
  const [medsById, setMedsById] = useState({})

  const loadReqRef = useRef(0)

  useEffect(() => {
    let active = true
    Promise.all([
      patientsApi.list({ page: 1, limit: 100 }),
      inventoryApi.listMedications({ page: 1, limit: 100 }),
    ])
      .then(([pats, meds]) => {
        if (!active) return
        setPatientsById(Object.fromEntries((pats.data || []).map((p) => [p.id, p])))
        setMedsById(Object.fromEntries((meds.data || []).map((m) => [m.id, m])))
      })
      .catch(() => {
        /* sin catálogos las filas muestran el id */
      })
    return () => {
      active = false
    }
  }, [])

  async function load(statusKey = chip) {
    const req = ++loadReqRef.current
    setLoading(true)
    try {
      const status = CHIPS.find((c) => c.key === statusKey)?.status
      const res = await prescriptionsApi.list({ status_filter: status || undefined, limit: 100 })
      if (loadReqRef.current !== req) return
      setPrescriptions(res.data || [])
    } catch (err) {
      if (loadReqRef.current !== req) return
      showToast('Error al cargar recetas', err.message, 'danger')
    } finally {
      if (loadReqRef.current === req) setLoading(false)
    }
  }

  useEffect(() => {
    load(chip)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chip])

  function patientLabel(r) {
    const p = patientsById[r.patientId]
    return p ? fullName(p) : r.patientId ?? '—'
  }

  function patientRut(r) {
    return patientsById[r.patientId]?.rut || ''
  }

  function medicationLabel(r) {
    const it = r.items?.[0]
    if (!it) return '—'
    return medsById[it.medicationId]?.description || it.medicationId || '—'
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return prescriptions
    return prescriptions.filter((r) => {
      const hay = [patientLabel(r), patientRut(r), medicationLabel(r)]
        .join(' ')
        .toLowerCase()
      return hay.includes(q)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prescriptions, search, patientsById, medsById])

  async function runAction(id, fn, okTitle) {
    setBusyId(id)
    try {
      await fn()
      showToast(okTitle, `Receta ${id} actualizada.`, 'success')
      await load(chip)
    } catch (err) {
      showToast('No se pudo completar la acción', err.message, 'danger')
    } finally {
      setBusyId(null)
    }
  }

  function openCancel(r) {
    setCancelReason('')
    setCancelRx(r)
  }

  async function submitCancel() {
    if (!cancelReason.trim()) {
      showToast('Falta el motivo', 'Indica el motivo de la anulación.', 'warning')
      return
    }
    const rx = cancelRx
    setCancelRx(null)
    await runAction(rx.id, () => prescriptionsApi.cancel(rx.id, { reason: cancelReason.trim() }), 'Receta anulada')
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Gestión de Recetas</h1>
          <p>Control de medicamentos recetados para pacientes</p>
        </div>
      </header>

      <div className="card">
        <div className="row-between mb-3">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Buscar paciente, RUT o medicamento"
          />
          <div className="chips" style={{ margin: 0 }}>
            {CHIPS.map((c) => (
              <button
                key={c.key}
                className={`chip${chip === c.key ? ' active' : ''}`}
                onClick={() => setChip(c.key)}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <Empty>Cargando recetas…</Empty>
        ) : filtered.length === 0 ? (
          <Empty>No hay recetas para mostrar.</Empty>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Paciente</th>
                <th>Medicamento</th>
                <th>Cantidad</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const st = prescriptionStatus(r.status)
                const acts = allowedActions(r.status)
                const rut = patientRut(r)
                const busy = busyId === r.id
                return (
                  <tr key={r.id}>
                    <td><strong>{r.id}</strong></td>
                    <td>
                      {patientLabel(r)}
                      {rut && <><br /><small>{rut}</small></>}
                    </td>
                    <td>{medicationLabel(r)}</td>
                    <td>{totalQuantity(r)}</td>
                    <td><Badge type={st.badge}>{st.label}</Badge></td>
                    <td className="actions">
                      {acts.includes('prepare') && (
                        <button
                          className="btn btn-success btn-sm"
                          disabled={busy}
                          onClick={() => runAction(r.id, () => prescriptionsApi.prepare(r.id), 'Receta preparada')}
                        >
                          Preparar
                        </button>
                      )}
                      {acts.includes('reserve') && (
                        <button
                          className="btn btn-warning btn-sm"
                          disabled={busy}
                          onClick={() => runAction(r.id, () => prescriptionsApi.reserve(r.id), 'Receta reservada')}
                        >
                          Reservar
                        </button>
                      )}
                      {acts.includes('markAvailable') && (
                        <button
                          className="btn btn-success btn-sm"
                          disabled={busy}
                          onClick={() => runAction(r.id, () => prescriptionsApi.markAvailable(r.id), 'Marcada disponible')}
                        >
                          Marcar disponible
                        </button>
                      )}
                      {acts.includes('deliver') && (
                        <button
                          className="btn btn-success btn-sm"
                          disabled={busy}
                          onClick={() => setPickup(r)}
                        >
                          Confirmar Retiro
                        </button>
                      )}
                      {acts.includes('cancel') && (
                        <button
                          className="btn btn-danger btn-sm"
                          disabled={busy}
                          onClick={() => openCancel(r)}
                        >
                          Anular
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

      <DeliverModal
        prescription={pickup}
        subtitle={pickup ? `${patientLabel(pickup)} · ${medicationLabel(pickup)}` : ''}
        onClose={() => setPickup(null)}
        onDelivered={() => {
          setPickup(null)
          load(chip)
        }}
      />

      <Modal
        open={!!cancelRx}
        onClose={() => setCancelRx(null)}
        title="Anular receta"
        subtitle={cancelRx ? `Receta ${cancelRx.id} · ${patientLabel(cancelRx)}` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setCancelRx(null)}>
              Cancelar
            </button>
            <button className="btn btn-danger" onClick={submitCancel}>
              Anular receta
            </button>
          </>
        }
      >
        <div className="input-group">
          <label htmlFor="cancel-reason">Motivo de anulación</label>
          <input
            id="cancel-reason"
            className="input"
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="Motivo de la anulación"
          />
        </div>
      </Modal>
    </>
  )
}
