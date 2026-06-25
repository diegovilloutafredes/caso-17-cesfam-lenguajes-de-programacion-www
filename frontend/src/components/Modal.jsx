import { useEffect } from 'react'

// Modal reutilizable: backdrop, cierre con Escape y click afuera.
export default function Modal({ open, onClose, title, subtitle, children, actions, large = false }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal${large ? ' modal-lg' : ''}`}>
        {title && <h2>{title}</h2>}
        {subtitle && <p className="modal-sub">{subtitle}</p>}
        {children}
        {actions && <div className="modal-actions">{actions}</div>}
      </div>
    </div>
  )
}
