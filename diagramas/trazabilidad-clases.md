# Diagrama de clases ↔ implementación

El diagrama de clases (`Caso17_Diagrama_Clases.drawio`) modela el dominio. Esta nota explica
cómo cada elemento se realiza en los microservicios, para cerrar la trazabilidad diseño →
código (C7). El diagrama se alineó con la implementación y con el diagrama v2 de
infraestructura/datos (que ya usaba `VARCHAR` y columnas embebidas).

## Identidad: claves naturales (String)

Las entidades persistidas usan **claves naturales String**, no enteros autoincrementales:
`PAT-001`, `USR-001`, `R001`, `MED-0001`, `BCH-001`, `WOF-001`, `GRD-001`, `NTF-001`. La
única PK entera real es `prescription_items.id` (autoincrement), entidad hija de
`Prescription`. Por eso el diagrama dice `id: String`.

## Value objects embebidos (no son tablas)

- **Stock** → columnas `availableQuantity`, `reservedQuantity`, `physicalQuantity` en
  `medications`. El comportamiento (`increment` / `reserve` / `isCritical`) vive en el
  servicio de inventario, no en una tabla aparte.
- **PatientCard** → columnas `patientCardNumber`, `patientCardIssueDate` en `patients`.
- **MedicationDelivery** y **DeliveryBatch** → se embeben como JSON (`delivery`) en
  `prescriptions`: `{ pickerType, guardianId, thirdPartyRut, thirdPartyName,
  batches: [{ batchId, quantity }], deliveryDate }`.

Se marcan «value object»: no tienen identidad ni ciclo de vida propios, viven dentro de su
agregado.

## Derivados / on-demand (no se persisten)

- **MedicationLog** (la "libreta") → no hay tabla; se **calcula** agregando las recetas del
  paciente (`GET /patients/{id}/history`). Marcado «derivada».
- **Report** → `report_service` no tiene modelos; el informe se genera **on-demand** como
  CSV. Marcado «no persistido».

## Por qué

Es coherente con los bounded contexts: las referencias entre servicios son por id (no hay FK
cross-contexto), los detalles de una entrega se embeben porque no tienen sentido fuera de su
receta, y la libreta y los informes se derivan para no duplicar estado.
