import { useEffect, useMemo, useState } from 'react'
import { prescriptionsApi, inventoryApi } from '../api'
import Modal from '../components/Modal'
import { SearchBar, Badge, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { prescriptionStatus, fullName } from '../lib/format'

const CHIPS = [
  { key: 'ALL', label: 'Todas', status: null },
  { key: 'SUBMITTED', label: 'Ingresado', status: 'SUBMITTED' },
  { key: 'READY_FOR_PICKUP', label: 'Disponibles', status: 'READY_FOR_PICKUP' },
  { key: 'RESERVED', label: 'Reservado', status: 'RESERVED' },
]

// El paciente/medicamento pueden venir embebidos o como simple id según el backend.
function patientLabel(r) {
  if (r.patient) return fullName(r.patient)
  return r.patientName || (r.patientId != null ? `Paciente ${r.patientId}` : '—')
}

function patientRut(r) {
  return r.patient?.rut || r.patientRut || ''
}

function medicationLabel(r) {
  const it = r.items?.[0]
  if (!it) return '—'
  return it.medicationDescription || it.description || it.medicationName ||
    (it.medicationId != null ? `Medicamento ${it.medicationId}` : '—')
}

function totalQuantity(r) {
  if (!r.items?.length) return '—'
  return r.items.reduce((acc, it) => acc + (it.totalQuantity || 0), 0)
}

const EMPTY_PICKUP = { pickerType: 'patient', guardianId: '', thirdPartyRut: '', thirdPartyName: '', batchId: '', quantity: '' }

export default function Recetas() {
  const { showToast } = useToast()
  const [prescriptions, setPrescriptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [chip, setChip] = useState('ALL')
  const [search, setSearch] = useState('')

  const [busyId, setBusyId] = useState(null)

  // Estado del modal de retiro.
  const [pickup, setPickup] = useState(null) // receta seleccionada
  const [batches, setBatches] = useState([])
  const [form, setForm] = useState(EMPTY_PICKUP)
  const [delivering, setDelivering] = useState(false)

  async function load(statusKey = chip) {
    setLoading(true)
    try {
      const status = CHIPS.find((c) => c.key === statusKey)?.status
      const res = await prescriptionsApi.list({ status_filter: status || undefined, limit: 100 })
      setPrescriptions(res.data || [])
    } catch (err) {
      showToast('Error al cargar recetas', err.message, 'danger')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(chip)
  }, [chip])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return prescriptions
    return prescriptions.filter((r) => {
      const hay = [patientLabel(r), patientRut(r), medicationLabel(r)]
        .join(' ')
        .toLowerCase()
      return hay.includes(q)
    })
  }, [prescriptions, search])

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

  async function openPickup(r) {
    setPickup(r)
    setForm(EMPTY_PICKUP)
    setBatches([])
    const medId = r.items?.[0]?.medicationId
    if (medId == null) return
    try {
      const med = await inventoryApi.getMedication(medId)
      const list = (med.batches || []).filter((b) => (b.availableQuantity || 0) > 0)
      setBatches(list)
      if (list.length) setForm((f) => ({ ...f, batchId: String(list[0].id) }))
    } catch (err) {
      showToast('Error al cargar partidas', err.message, 'danger')
    }
  }

  function closePickup() {
    setPickup(null)
    setBatches([])
    setForm(EMPTY_PICKUP)
  }

  async function submitPickup() {
    if (!form.batchId) {
      showToast('Falta la partida', 'Seleccione una partida a entregar.', 'warning')
      return
    }
    const qty = Number(form.quantity)
    if (!qty || qty <= 0) {
      showToast('Cantidad inválida', 'Ingrese la cantidad a entregar.', 'warning')
      return
    }
    const body = {
      pickerType: form.pickerType === 'third-party' ? 'third_party' : form.pickerType,
      batches: [{ batchId: form.batchId, quantity: qty }],
    }
    if (form.pickerType === 'guardian') {
      if (!form.guardianId) {
        showToast('Falta el apoderado', 'Seleccione un apoderado autorizado.', 'warning')
        return
      }
      body.guardianId = form.guardianId
    }
    if (form.pickerType === 'third-party') {
      if (!form.thirdPartyRut || !form.thirdPartyName) {
        showToast('Datos del tercero incompletos', 'Ingrese RUT y nombre del tercero.', 'warning')
        return
      }
      body.thirdPartyRut = form.thirdPartyRut
      body.thirdPartyName = form.thirdPartyName
    }
    setDelivering(true)
    try {
      await prescriptionsApi.deliver(pickup.id, body)
      showToast('Retiro confirmado', `Receta ${pickup.id} entregada.`, 'success')
      closePickup()
      await load(chip)
    } catch (err) {
      showToast('No se pudo confirmar el retiro', err.message, 'danger')
    } finally {
      setDelivering(false)
    }
  }

  const guardians = pickup?.patient?.guardians || []

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
                      {r.status === 'SUBMITTED' && (
                        <>
                          <button
                            className="btn btn-success btn-sm"
                            disabled={busy}
                            onClick={() => runAction(r.id, () => prescriptionsApi.markAvailable(r.id), 'Marcada disponible')}
                          >
                            Marcar disponible
                          </button>
                          <button
                            className="btn btn-warning btn-sm"
                            disabled={busy}
                            onClick={() => runAction(r.id, () => prescriptionsApi.reserve(r.id), 'Receta reservada')}
                          >
                            Reservar
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            disabled={busy}
                            onClick={() => runAction(r.id, () => prescriptionsApi.cancel(r.id, { reason: 'Anulada desde recetas' }), 'Receta anulada')}
                          >
                            Anular
                          </button>
                        </>
                      )}
                      {r.status === 'RESERVED' && (
                        <button
                          className="btn btn-success btn-sm"
                          disabled={busy}
                          onClick={() => runAction(r.id, () => prescriptionsApi.markAvailable(r.id), 'Marcada disponible')}
                        >
                          Marcar disponible
                        </button>
                      )}
                      {r.status === 'READY_FOR_PICKUP' && (
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => openPickup(r)}
                        >
                          Confirmar Retiro
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

      <Modal
        open={!!pickup}
        onClose={closePickup}
        large
        title="Confirmar Retiro"
        subtitle={pickup ? `${patientLabel(pickup)} · ${medicationLabel(pickup)}` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={closePickup} disabled={delivering}>
              Cancelar
            </button>
            <button className="btn btn-success" onClick={submitPickup} disabled={delivering}>
              Confirmar Retiro
            </button>
          </>
        }
      >
        <div className="input-group">
          <label>¿Quién retira?</label>
          <div className="radio-list">
            <label className="radio-row">
              <input
                type="radio"
                name="picker-type"
                value="patient"
                checked={form.pickerType === 'patient'}
                onChange={() => setForm((f) => ({ ...f, pickerType: 'patient' }))}
              />{' '}
              El propio paciente
            </label>

            <label className="radio-row">
              <input
                type="radio"
                name="picker-type"
                value="guardian"
                checked={form.pickerType === 'guardian'}
                onChange={() => setForm((f) => ({ ...f, pickerType: 'guardian' }))}
              />{' '}
              Un apoderado autorizado
            </label>
            <select
              className="select subfield-indent"
              disabled={form.pickerType !== 'guardian'}
              value={form.guardianId}
              onChange={(e) => setForm((f) => ({ ...f, guardianId: e.target.value }))}
            >
              <option value="">Seleccione apoderado…</option>
              {guardians.map((g) => (
                <option key={g.id} value={g.id}>
                  {fullName(g)}{g.relationship ? ` (${g.relationship})` : ''}{g.rut ? ` — ${g.rut}` : ''}
                </option>
              ))}
            </select>

            <label className="radio-row">
              <input
                type="radio"
                name="picker-type"
                value="third-party"
                checked={form.pickerType === 'third-party'}
                onChange={() => setForm((f) => ({ ...f, pickerType: 'third-party' }))}
              />{' '}
              Un tercero autorizado verbalmente
            </label>
            <div className="grid grid-2 subfield-indent">
              <div className="input-group">
                <label>RUT del tercero</label>
                <input
                  className="input"
                  type="text"
                  placeholder="12.345.678-9"
                  disabled={form.pickerType !== 'third-party'}
                  value={form.thirdPartyRut}
                  onChange={(e) => setForm((f) => ({ ...f, thirdPartyRut: e.target.value }))}
                />
              </div>
              <div className="input-group">
                <label>Nombre completo</label>
                <input
                  className="input"
                  type="text"
                  placeholder="Nombre Apellido"
                  disabled={form.pickerType !== 'third-party'}
                  value={form.thirdPartyName}
                  onChange={(e) => setForm((f) => ({ ...f, thirdPartyName: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-2 mt-3">
          <div className="input-group">
            <label>Partida a entregar (FEFO — vence primero)</label>
            <select
              className="select"
              value={form.batchId}
              onChange={(e) => setForm((f) => ({ ...f, batchId: e.target.value }))}
            >
              {batches.length === 0 && <option value="">Sin partidas disponibles</option>}
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.batchNumber} — vence {b.expirationDate} — disponible: {b.availableQuantity}
                </option>
              ))}
            </select>
          </div>
          <div className="input-group">
            <label>Cantidad a entregar</label>
            <input
              className="input"
              type="number"
              min="1"
              placeholder="0"
              value={form.quantity}
              onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
            />
          </div>
        </div>
      </Modal>
    </>
  )
}
