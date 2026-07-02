import { useEffect, useRef, useState } from 'react'
import { patientsApi } from '../api'
import Modal from '../components/Modal'
import ActivePrescriptionsList from '../components/ActivePrescriptionsList'
import { SearchBar, Badge, Empty } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { fullName } from '../lib/format'

const LIMIT = 8

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

  // Invalida respuestas tardías: si se cerró el modal o se pidió otro paciente,
  // la carga en vuelo se descarta en vez de reabrirlo.
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
                      Ver info
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
          <button className="btn btn-outline" onClick={closeInfo}>
            Cerrar
          </button>
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
            </div>

            <ActivePrescriptionsList
              prescriptions={activePrescriptions}
              renderTitle={(rx) => `Receta #${rx.id}`}
              renderMeta={(rx) =>
                `${rx.items?.length || 0} medicamento(s)${rx.pickupDeadline ? ` · Retiro hasta ${rx.pickupDeadline}` : ''}`
              }
            />

            <div className="modal-section">
              <h3>Apoderados autorizados</h3>
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
                      </small>
                    </div>
                    <Badge type="muted">Activo</Badge>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </Modal>
    </>
  )
}
