import { useEffect, useRef, useState } from 'react'
import { inventoryApi, patientsApi, prescriptionsApi } from '../api'
import Modal from './Modal'
import { useToast } from '../context/ToastContext'
import { fullName } from '../lib/format'

const EMPTY_FORM = {
  pickerType: 'patient',
  guardianId: '',
  thirdPartyRut: '',
  thirdPartyName: '',
  batchId: '',
  quantity: '',
}

// Modal de retiro compartido por Recetas y Panel Farmacia.
export default function DeliverModal({ prescription, subtitle, onClose, onDelivered }) {
  const { showToast } = useToast()
  const [form, setForm] = useState(EMPTY_FORM)
  const [batches, setBatches] = useState([])
  const [guardians, setGuardians] = useState([])
  const [delivering, setDelivering] = useState(false)
  const reqRef = useRef(0)

  useEffect(() => {
    if (!prescription) return
    const req = ++reqRef.current
    setForm(EMPTY_FORM)
    setBatches([])
    setGuardians([])
    const item = prescription.items?.[0]
    const required = item?.totalQuantity || 0

    async function loadData() {
      try {
        const [med, guardianList] = await Promise.all([
          item?.medicationId != null
            ? inventoryApi.getMedication(item.medicationId)
            : Promise.resolve(null),
          patientsApi.listGuardians(prescription.patientId),
        ])
        if (reqRef.current !== req) return
        const today = new Date().toISOString().slice(0, 10)
        const list = (med?.batches || [])
          .filter((b) => (b.availableQuantity || 0) > 0 && (b.expirationDate || '') >= today)
          .sort((a, b) => (a.expirationDate || '').localeCompare(b.expirationDate || ''))
        setBatches(list)
        setGuardians(guardianList || [])
        // La entrega es completa: prellena la cantidad recetada y una partida con stock suficiente.
        const batch = list.find((b) => b.availableQuantity >= required) || list[0]
        setForm((f) => ({
          ...f,
          quantity: String(required || ''),
          batchId: batch ? String(batch.id) : '',
        }))
      } catch (err) {
        if (reqRef.current !== req) return
        showToast('Error al cargar datos del retiro', err.message, 'danger')
      }
    }
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prescription])

  function close() {
    reqRef.current++
    onClose()
  }

  async function submit() {
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
      pickerType: form.pickerType,
      batches: [{ batchId: form.batchId, quantity: qty }],
    }
    if (form.pickerType === 'guardian') {
      if (!form.guardianId) {
        showToast('Falta el apoderado', 'Seleccione un apoderado autorizado.', 'warning')
        return
      }
      body.guardianId = form.guardianId
    }
    if (form.pickerType === 'third_party') {
      if (!form.thirdPartyRut || !form.thirdPartyName) {
        showToast('Datos del tercero incompletos', 'Ingrese RUT y nombre del tercero.', 'warning')
        return
      }
      body.thirdPartyRut = form.thirdPartyRut
      body.thirdPartyName = form.thirdPartyName
    }
    setDelivering(true)
    try {
      await prescriptionsApi.deliver(prescription.id, body)
      showToast('Retiro confirmado', `Receta ${prescription.id} entregada.`, 'success')
      onDelivered()
    } catch (err) {
      showToast('No se pudo confirmar el retiro', err.message, 'danger')
    } finally {
      setDelivering(false)
    }
  }

  return (
    <Modal
      open={!!prescription}
      onClose={close}
      large
      title="Confirmar Retiro"
      subtitle={subtitle}
      actions={
        <>
          <button className="btn btn-outline" onClick={close} disabled={delivering}>
            Cancelar
          </button>
          <button className="btn btn-success" onClick={submit} disabled={delivering}>
            {delivering ? 'Registrando…' : 'Confirmar Retiro'}
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
            aria-label="Apoderado que retira"
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
              value="third_party"
              checked={form.pickerType === 'third_party'}
              onChange={() => setForm((f) => ({ ...f, pickerType: 'third_party' }))}
            />{' '}
            Un tercero autorizado verbalmente
          </label>
          <div className="grid grid-2 subfield-indent">
            <div className="input-group">
              <label htmlFor="deliver-third-rut">RUT del tercero</label>
              <input
                id="deliver-third-rut"
                className="input"
                type="text"
                placeholder="12.345.678-9"
                disabled={form.pickerType !== 'third_party'}
                value={form.thirdPartyRut}
                onChange={(e) => setForm((f) => ({ ...f, thirdPartyRut: e.target.value }))}
              />
            </div>
            <div className="input-group">
              <label htmlFor="deliver-third-name">Nombre completo</label>
              <input
                id="deliver-third-name"
                className="input"
                type="text"
                placeholder="Nombre Apellido"
                disabled={form.pickerType !== 'third_party'}
                value={form.thirdPartyName}
                onChange={(e) => setForm((f) => ({ ...f, thirdPartyName: e.target.value }))}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-2 mt-3">
        <div className="input-group">
          <label htmlFor="deliver-batch">Partida a entregar (FEFO — vence primero)</label>
          <select
            id="deliver-batch"
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
          <label htmlFor="deliver-quantity">Cantidad a entregar</label>
          <input
            id="deliver-quantity"
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
  )
}
