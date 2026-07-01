// Fuente única de verdad de las transiciones de estado de una receta, espejo de la
// máquina de estados del backend (prescription_service). Cada pantalla muestra solo los
// botones cuya acción está permitida en el estado actual; el backend igual valida.
export function allowedActions(status) {
  switch (status) {
    case 'SUBMITTED':
      return ['prepare', 'reserve', 'external', 'cancel']
    case 'RESERVED':
      return ['markAvailable', 'cancel']
    case 'READY_FOR_PICKUP':
      return ['deliver', 'cancel']
    default:
      return [] // terminales: PICKED_UP, CANCELLED, EXPIRED, EXTERNAL_PURCHASE
  }
}
