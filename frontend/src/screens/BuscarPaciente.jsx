import { useEffect, useRef, useState } from 'react'
import { patientsApi } from '../api'
import Modal from '../components/Modal'
import ActivePrescriptionsList from '../components/ActivePrescriptionsList'
import { SearchBar, Badge, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { fullName } from '../lib/format'

const LIMIT = 8

const EMPTY_GUARDIAN = { rut: '', firstName: '', lastName: '', relationship: '', phone: '', email: '' }

const paginationStyles = `
.bp-pagination { display:flex; gap:6px; justify-content:center; margin-top:24px; flex-wrap:wrap; }
.bp-pagination button { width:36px; height:36px; border-radius:8px; border:1px solid var(--border); background:#fff; cursor:pointer; }
.bp-pagination button.active { background: var(--brand); color:#fff; border-color: var(--brand); }
.bp-pagination button:disabled { opacity:.5; cursor:default; }
.bp-pagination .gap { width:36px; display:grid; place-items:center; color:var(--text-soft); }
`

function pageItems(current, totalPages) {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1)
  const items = new Set([1, 2, totalPages - 1, totalPages, current])
  if (current > 1) items.add(current - 1)
  if (current < totalPages) items.add(current + 1)
  const sorted = [...items].filter((n) => n >= 1 && n <= totalPages).sort((a, b) => a - b)
  const result = []
  let prev = 0
  for (const n of sorted) {
    if (n - prev > 1) result.push('gap')
    result.push(n)
    prev = n
  }
  return result
}

export default function BuscarPaciente() {
  const { showToast } = useToast()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  const [selected, setSelected] = useState(null)
  const [history, setHistory] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Edición de la ficha (los datos identificatorios como el RUT no se editan).
  const [editOpen, setEditOpen] = useState(false)
  const [editForm, setEditForm] = useState({ firstName: '', lastName: '', address: '', phone: '', email: '' })

  // Gestión de apoderados.
  const [guardianOpen, setGuardianOpen] = useState(false)
  const [guardianForm, setGuardianForm] = useState(EMPTY_GUARDIAN)
  const [removing, setRemoving] = useState(null) // apoderado a quitar (confirmación)

  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    const t = setTimeout(() => {
      patientsApi
        .list({ search, page, limit: LIMIT })
        .then((res) => {
          if (!active) return
          setRows(res.data || [])
          setTotal(res.pagination?.total || 0)
        })
        .catch((err) => {
          if (!active) return
          setRows([])
          setTotal(0)
          showToast('Error al buscar pacientes', err.message, 'danger')
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 300)
    return () => {
      active = false
      clearTimeout(t)
    }
  }, [search, page, showToast])

  function onSearchChange(value) {
    setSearch(value)
    setPage(1)
  }

  // descarta respuestas tardías para que el modal no se reabra solo
  const infoReqRef = useRef(0)

  async function openInfo(patientId) {
    const req = ++infoReqRef.current
    setSelected(null)
    setHistory(null)
    setDetailLoading(true)
    try {
      const [patient, hist] = await Promise.all([
        patientsApi.get(patientId),
        patientsApi.history(patientId),
      ])
      if (infoReqRef.current !== req) return
      setSelected(patient)
      setHistory(hist)
    } catch (err) {
      if (infoReqRef.current !== req) return
      showToast('Error al cargar paciente', err.message, 'danger')
      setSelected(null)
    } finally {
      if (infoReqRef.current === req) setDetailLoading(false)
    }
  }

  function closeInfo() {
    infoReqRef.current++
    setSelected(null)
    setHistory(null)
    setDetailLoading(false)
  }

  // Recarga la ficha tras una mutación, sin cerrar el modal de detalle.
  async function refreshPatient(patientId) {
    const req = infoReqRef.current
    try {
      const fresh = await patientsApi.get(patientId)
      if (infoReqRef.current === req) setSelected(fresh)
    } catch {
      /* la ficha queda con los datos previos */
    }
  }

  function openEdit() {
    setEditForm({
      firstName: selected.firstName || '',
      lastName: selected.lastName || '',
      address: selected.address || '',
      phone: selected.phone || '',
      email: selected.email || '',
    })
    setEditOpen(true)
  }

  async function submitEdit() {
    if (!editForm.firstName.trim() || !editForm.lastName.trim()) {
      showToast('Faltan datos', 'El nombre y el apellido son obligatorios.', 'warning')
      return
    }
    setSaving(true)
    try {
      await patientsApi.update(selected.id, {
        firstName: editForm.firstName.trim(),
        lastName: editForm.lastName.trim(),
        address: editForm.address.trim() || null,
        phone: editForm.phone.trim() || null,
        email: editForm.email.trim() || null,
      })
      setEditOpen(false)
      showToast('Ficha actualizada', 'Los datos del paciente quedaron al día.', 'success')
      await refreshPatient(selected.id)
    } catch (err) {
      showToast('Error al actualizar la ficha', err.message, 'danger')
    } finally {
      setSaving(false)
    }
  }

  function openAddGuardian() {
    setGuardianForm(EMPTY_GUARDIAN)
    setGuardianOpen(true)
  }

  async function submitGuardian() {
    if (!guardianForm.rut.trim() || !guardianForm.firstName.trim() ||
        !guardianForm.lastName.trim() || !guardianForm.relationship.trim()) {
      showToast('Faltan datos', 'RUT, nombre, apellido y parentesco son obligatorios.', 'warning')
      return
    }
    setSaving(true)
    try {
      await patientsApi.addGuardian(selected.id, {
        rut: guardianForm.rut.trim(),
        firstName: guardianForm.firstName.trim(),
        lastName: guardianForm.lastName.trim(),
        relationship: guardianForm.relationship.trim(),
        phone: guardianForm.phone.trim() || null,
        email: guardianForm.email.trim() || null,
      })
      setGuardianOpen(false)
      showToast('Apoderado registrado', `Queda autorizado para retirar por ${fullName(selected)}.`, 'success')
      await refreshPatient(selected.id)
    } catch (err) {
      showToast('Error al registrar apoderado', err.message, 'danger')
    } finally {
      setSaving(false)
    }
  }

  async function submitRemoveGuardian() {
    setSaving(true)
    try {
      await patientsApi.removeGuardian(selected.id, removing.id)
      setRemoving(null)
      showToast('Apoderado eliminado', 'Ya no está autorizado para retirar.', 'warning')
      await refreshPatient(selected.id)
    } catch (err) {
      showToast('Error al quitar apoderado', err.message, 'danger')
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / LIMIT))
  const items = pageItems(page, totalPages)
  const activePrescriptions = history?.activePrescriptions || []
  const guardians = selected?.guardians || []

  return (
    <>
      <style>{paginationStyles}</style>

      <header className="page-header">
        <div>
          <h1>Buscar paciente</h1>
        </div>
      </header>

      <div className="card">
        <SearchBar
          value={search}
          onChange={onSearchChange}
          placeholder="Buscar paciente por nombre o RUT..."
          style={{ maxWidth: 'none', marginBottom: 12 }}
        />

        {loading ? (
          <Empty>Cargando pacientes...</Empty>
        ) : rows.length === 0 ? (
          <Empty>No se encontraron pacientes.</Empty>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>RUT</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td>{fullName(p)}</td>
                  <td>{p.rut}</td>
                  <td>
                    <button className="btn btn-primary btn-sm" onClick={() => openInfo(p.id)}>
                      Ver detalle
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && totalPages > 1 && (
          <nav className="bp-pagination" aria-label="Paginación">
            {items.map((it, i) =>
              it === 'gap' ? (
                <span className="gap" key={`gap-${i}`}>
                  …
                </span>
              ) : (
                <button
                  key={it}
                  className={it === page ? 'active' : ''}
                  onClick={() => setPage(it)}
                >
                  {it}
                </button>
              ),
            )}
          </nav>
        )}
      </div>

      <Modal
        open={detailLoading || !!selected}
        onClose={closeInfo}
        large
        title="Información del paciente"
        subtitle="Carnet de paciente, recetas activas y apoderados."
        actions={
          <>
            <button className="btn btn-outline" onClick={closeInfo}>
              Cerrar
            </button>
            {selected && (
              <button className="btn btn-primary" onClick={openEdit}>
                Editar ficha
              </button>
            )}
          </>
        }
      >
        {detailLoading || !selected ? (
          <Empty>Cargando información del paciente...</Empty>
        ) : (
          <>
            <div className="grid grid-2">
              <div className="input-group">
                <label>Nombre completo</label>
                <input className="input" type="text" value={fullName(selected)} readOnly />
              </div>
              <div className="input-group">
                <label>RUT</label>
                <input className="input" type="text" value={selected.rut || ''} readOnly />
              </div>
              <div className="input-group">
                <label>Fecha de nacimiento</label>
                <input className="input" type="text" value={selected.birthDate || ''} readOnly />
              </div>
              <div className="input-group">
                <label>Carnet de Paciente</label>
                <input
                  className="input"
                  type="text"
                  value={selected.patientCard?.number || ''}
                  readOnly
                />
              </div>
              <div className="input-group">
                <label>Teléfono</label>
                <input className="input" type="text" value={selected.phone || ''} readOnly />
              </div>
              <div className="input-group">
                <label>Email</label>
                <input className="input" type="text" value={selected.email || ''} readOnly />
              </div>
              <div className="input-group" style={{ gridColumn: 'span 2' }}>
                <label>Dirección</label>
                <input className="input" type="text" value={selected.address || ''} readOnly />
              </div>
            </div>

            <ActivePrescriptionsList
              prescriptions={activePrescriptions}
              renderTitle={(rx) => `Receta #${rx.id}`}
              renderMeta={(rx) =>
                `${rx.items?.length || 0} medicamento(s)${rx.pickupDeadline ? ` · Retiro hasta ${rx.pickupDeadline}` : ''}`
              }
            />

            <div className="modal-section">
              <div className="row-between" style={{ marginBottom: 10 }}>
                <h3 style={{ margin: 0 }}>Apoderados autorizados</h3>
                <button className="btn btn-primary btn-sm" onClick={openAddGuardian}>
                  ＋ Añadir apoderado
                </button>
              </div>
              {guardians.length === 0 ? (
                <Empty>Sin apoderados registrados.</Empty>
              ) : (
                guardians.map((g) => (
                  <div className="apoderado-row" key={g.id}>
                    <div className="meta">
                      <strong>{fullName(g)}</strong>
                      <small>
                        {g.rut}
                        {g.relationship ? ` · ${g.relationship}` : ''}
                        {g.authorizationDate ? ` · autorizado desde ${g.authorizationDate}` : ''}
                      </small>
                    </div>
                    <div className="row" style={{ gap: 8 }}>
                      <Badge type="muted">Activo</Badge>
                      <button className="btn btn-outline btn-sm" onClick={() => setRemoving(g)}>
                        Quitar
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </Modal>

      {/* Modal: editar ficha del paciente */}
      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title="Editar ficha del paciente"
        subtitle={selected ? `${fullName(selected)} · ${selected.rut}` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setEditOpen(false)} disabled={saving}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={submitEdit} disabled={saving}>
              {saving ? 'Guardando…' : 'Guardar cambios'}
            </button>
          </>
        }
      >
        <div className="grid grid-2">
          <div className="input-group">
            <label htmlFor="edit-first-name">Nombre</label>
            <input
              id="edit-first-name"
              className="input"
              value={editForm.firstName}
              onChange={(e) => setEditForm({ ...editForm, firstName: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="edit-last-name">Apellido</label>
            <input
              id="edit-last-name"
              className="input"
              value={editForm.lastName}
              onChange={(e) => setEditForm({ ...editForm, lastName: e.target.value })}
            />
          </div>
          <div className="input-group" style={{ gridColumn: 'span 2' }}>
            <label htmlFor="edit-address">Dirección</label>
            <input
              id="edit-address"
              className="input"
              placeholder="Calle y número, comuna"
              value={editForm.address}
              onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="edit-phone">Teléfono</label>
            <input
              id="edit-phone"
              className="input"
              placeholder="+56 9 1234 5678"
              value={editForm.phone}
              onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="edit-email">Email</label>
            <input
              id="edit-email"
              className="input"
              type="email"
              placeholder="nombre@correo.cl"
              value={editForm.email}
              onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
            />
          </div>
        </div>
        <p className="text-soft" style={{ marginBottom: 0 }}>
          El RUT y la fecha de nacimiento son datos identificatorios y no se modifican.
        </p>
      </Modal>

      {/* Modal: añadir apoderado */}
      <Modal
        open={guardianOpen}
        onClose={() => setGuardianOpen(false)}
        title="Añadir apoderado"
        subtitle={selected ? `Autorizado para retirar medicamentos por ${fullName(selected)}.` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setGuardianOpen(false)} disabled={saving}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={submitGuardian} disabled={saving}>
              {saving ? 'Registrando…' : 'Registrar apoderado'}
            </button>
          </>
        }
      >
        <div className="grid grid-2">
          <div className="input-group">
            <label htmlFor="guardian-rut">RUT</label>
            <input
              id="guardian-rut"
              className="input"
              placeholder="12.345.678-9"
              value={guardianForm.rut}
              onChange={(e) => setGuardianForm({ ...guardianForm, rut: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="guardian-relationship">Parentesco</label>
            <input
              id="guardian-relationship"
              className="input"
              placeholder="Hijo, esposa, cuidador…"
              value={guardianForm.relationship}
              onChange={(e) => setGuardianForm({ ...guardianForm, relationship: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="guardian-first-name">Nombre</label>
            <input
              id="guardian-first-name"
              className="input"
              value={guardianForm.firstName}
              onChange={(e) => setGuardianForm({ ...guardianForm, firstName: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="guardian-last-name">Apellido</label>
            <input
              id="guardian-last-name"
              className="input"
              value={guardianForm.lastName}
              onChange={(e) => setGuardianForm({ ...guardianForm, lastName: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="guardian-phone">Teléfono (opcional)</label>
            <input
              id="guardian-phone"
              className="input"
              placeholder="+56 9 1234 5678"
              value={guardianForm.phone}
              onChange={(e) => setGuardianForm({ ...guardianForm, phone: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label htmlFor="guardian-email">Email (opcional)</label>
            <input
              id="guardian-email"
              className="input"
              type="email"
              placeholder="nombre@correo.cl"
              value={guardianForm.email}
              onChange={(e) => setGuardianForm({ ...guardianForm, email: e.target.value })}
            />
          </div>
        </div>
      </Modal>

      {/* Modal: quitar apoderado */}
      <Modal
        open={!!removing}
        onClose={() => setRemoving(null)}
        title="Quitar apoderado"
        subtitle={removing ? `${fullName(removing)} (${removing.rut}) dejará de estar autorizado.` : ''}
        actions={
          <>
            <button className="btn btn-outline" onClick={() => setRemoving(null)} disabled={saving}>
              Cancelar
            </button>
            <button className="btn btn-danger" onClick={submitRemoveGuardian} disabled={saving}>
              {saving ? 'Quitando…' : 'Quitar autorización'}
            </button>
          </>
        }
      >
        <p className="text-soft" style={{ margin: 0 }}>
          No podrá retirar medicamentos por este paciente hasta que se registre de nuevo.
        </p>
      </Modal>
    </>
  )
}
