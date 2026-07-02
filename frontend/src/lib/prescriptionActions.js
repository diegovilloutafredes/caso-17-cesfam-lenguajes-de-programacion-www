// debe calzar con las transiciones de prescription_service
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
