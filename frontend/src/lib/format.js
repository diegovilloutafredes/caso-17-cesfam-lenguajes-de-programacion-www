// Mapeos de estado → etiqueta + clase de badge (fieles al prototipo).

export const PRESCRIPTION_STATUS = {
  SUBMITTED: { label: 'Ingresado', badge: 'info' },
  RESERVED: { label: 'Reservado', badge: 'warning' },
  READY_FOR_PICKUP: { label: 'Disponible', badge: 'success' },
  PICKED_UP: { label: 'Retirado', badge: 'muted' },
  EXTERNAL_PURCHASE: { label: 'Compra externa', badge: 'muted' },
  CANCELLED: { label: 'Anulada', badge: 'danger' },
  EXPIRED: { label: 'Vencida', badge: 'muted' },
}

export const STOCK_STATUS = {
  AVAILABLE: { label: 'Disponible', badge: 'success' },
  LOW_STOCK: { label: 'Stock bajo', badge: 'warning' },
  OUT_OF_STOCK: { label: 'Sin stock', badge: 'danger' },
}

export function prescriptionStatus(s) {
  return PRESCRIPTION_STATUS[s] || { label: s, badge: 'muted' }
}

export function stockStatus(s) {
  return STOCK_STATUS[s] || { label: s, badge: 'muted' }
}

export function fullName(p) {
  if (!p) return ''
  return [p.firstName, p.lastName].filter(Boolean).join(' ')
}

export function initials(name) {
  if (!name) return '?'
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}
