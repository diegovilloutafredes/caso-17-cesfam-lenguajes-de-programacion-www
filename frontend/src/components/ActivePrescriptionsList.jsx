import { Badge, Empty } from './ui'
import { prescriptionStatus } from '../lib/format'

export default function ActivePrescriptionsList({
  prescriptions,
  renderTitle = (rx) => rx.id,
  renderMeta = () => '',
  title = 'Recetas activas',
}) {
  const list = prescriptions || []
  return (
    <div className="modal-section">
      <h3>{title}</h3>
      {list.length === 0 ? (
        <Empty>Sin recetas activas.</Empty>
      ) : (
        list.map((rx) => {
          const st = prescriptionStatus(rx.status)
          return (
            <div className="apoderado-row" key={rx.id}>
              <div className="meta">
                <strong>{renderTitle(rx)}</strong>
                <small>{renderMeta(rx)}</small>
              </div>
              <Badge type={st.badge}>{st.label}</Badge>
            </div>
          )
        })
      )}
    </div>
  )
}
