import { useEffect, useRef } from 'react'

// Con modales apilados, Escape debe cerrar solo el de más arriba.
const openModals = []

export default function Modal({ open, onClose, title, subtitle, children, actions, large = false }) {
  const idRef = useRef({})
  const boxRef = useRef(null)
  // el efecto depende solo de `open`: si dependiera de onClose (inestable en los
  // call sites), cada tecla re-suscribiría y el focus() le robaría el foco al input
  const onCloseRef = useRef(onClose)
  useEffect(() => {
    onCloseRef.current = onClose
  })

  useEffect(() => {
    if (!open) return
    const id = idRef.current
    openModals.push(id)
    const onKey = (e) => {
      if (e.key === 'Escape' && openModals[openModals.length - 1] === id) onCloseRef.current()
    }
    document.addEventListener('keydown', onKey)
    boxRef.current?.focus()
    return () => {
      const i = openModals.indexOf(id)
      if (i >= 0) openModals.splice(i, 1)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div
        className={`modal${large ? ' modal-lg' : ''}`}
        role="dialog"
        aria-modal="true"
        tabIndex={-1}
        ref={boxRef}
      >
        {title && <h2>{title}</h2>}
        {subtitle && <p className="modal-sub">{subtitle}</p>}
        {children}
        {actions && <div className="modal-actions">{actions}</div>}
      </div>
    </div>
  )
}
