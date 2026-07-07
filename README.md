# Caso 17 — Automatización Libreta de Medicamentos CESFAM

**INF-301 Lenguajes de Programación en WWW · Universidad Santa María (USM)**

### Integrantes

- Benjamin Paulsen — 202173017-6
- Gaspar Navarro — 202173003-6
- Diego Villouta — 2773019-1
- Badir Villegas — 202273020-K
- Carolina Sire — 202173105-9
- Bastian Camus — 202173013-3

### Enlaces

- **Video final:** <https://www.youtube.com/watch?v=nlrzXA4pico>
- **Aplicación (desplegada):** <https://cesfam-frontend.vercel.app/login>
- **Taiga:** <https://tree.taiga.io/project/incuboyd-cesfam/timeline> (acceso también por invitación al correo)
- **Figma:** <https://www.figma.com/design/M4t15dslNRQUS57waoLyCF/Sin-t%C3%ADtulo?node-id=0-1&p=f&t=1nbznUF4WFuh8z8z-0>

---

## Backend de microservicios

Backend del sistema de **Automatización de Libreta de Medicamentos CESFAM**, implementado como arquitectura de microservicios.

---

## Inicio rápido (correr todo en local)

Requisitos: **Docker Desktop** (corriendo) y **Node 18+**.

```bash
make dev      # build + arranca el backend (7 servicios + Postgres) y el frontend
```

- App: <http://localhost:5173> · API/BFF: <http://localhost:8000>
- Login: `drperez / medico2026` (médico) · `mgonzalez / farmacia2026` (farmacia) · detener: `Ctrl+C` o `make stop`

`make dev` instala las dependencias solo: las del backend dentro de la imagen Docker
(`pip install`) y las del frontend (`npm install`).

---

## Tabla de contenidos

1. [Arquitectura y estructura de microservicios](#1-arquitectura-y-estructura-de-microservicios)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Servicios - URL, puerto y responsabilidad](#3-servicios--url-puerto-y-responsabilidad)
4. [Relaciones inter-servicio](#4-relaciones-inter-servicio)
5. [Requisitos previos](#5-requisitos-previos)
6. [Instalación y ejecución con Docker (recomendado)](#6-instalación-y-ejecución-con-docker-recomendado)
7. [Scripts disponibles - qué hace cada uno](#7-scripts-disponibles--qué-hace-cada-uno)
8. [Ejecución sin Docker (alternativa)](#8-ejecución-sin-docker-alternativa)
9. [Usuarios dummy para probar el sandbox](#9-usuarios-dummy-para-probar-el-sandbox)
10. [Datos iniciales (seed)](#10-datos-iniciales-seed)
11. [Cómo probar el sandbox](#11-cómo-probar-el-sandbox)

---

## 1. Arquitectura y estructura de microservicios

**7 procesos FastAPI** corriendo en containers Docker, cada uno con su propio dominio acotado (bounded context):

```
                Clientes HTTP (React/browser · Postman · curl)
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │   ApiGateway (BFF)    │ ← entrypoint
                      │         :8000         │
                      └───────────┬───────────┘
                                  │ HTTP + Bearer token
        ┌────────────┬────────────┼──────────────┬─────────────┐
        ▼            ▼            ▼              ▼             ▼
   ┌──────────┐ ┌─────────┐ ┌───────────┐ ┌──────────────┐ ┌────────┐
   │ Identity │ │ Patient │ │ Inventory │ │ Prescription │ │ Report │
   │  :8001   │ │  :8002  │ │   :8003   │ │    :8004     │ │ :8006  │
   └──────────┘ └────┬────┘ └───────────┘ └──────┬───────┘ └────────┘
                     │ HTTP                       │ HTTP → 3 servicios:
                     ▼                            ▼  Patient, Inventory,
                                                     Notification
               ┌──────────────┐         ┌────────────────────┐
               │ Prescription │         │ Notification :8005 │
               │    :8004     │         └────────────────────┘
               └──────────────┘
```

### Estructura del proyecto

```
backend-microservices/
├── docker-compose.yml              ← orquestación de 8 containers (PostgreSQL + 7 servicios)
├── Dockerfile                       ← imagen compartida (python:3.12-slim + deps)
├── .dockerignore
├── requirements.txt                 ← fastapi, uvicorn, pydantic, httpx, tenacity
│
├── install.sh / install.bat         ← scripts modo Docker
├── run.sh     / run.bat
├── stop.sh    / stop.bat
│
├── install-local.sh / install-local.bat   ← scripts modo SIN Docker
├── run-local.sh     / run-local.bat
├── stop-local.sh    / stop-local.bat
│
├── shared/                          ← código común a todos los servicios
│   ├── envelope.py                  ← ApiResponse<T> + helpers ok/created/fail
│   ├── auth.py                      ← Bearer stub + KNOWN_USERS
│   ├── http_client.py               ← ServiceClient base + CircuitBreaker + retry
│   └── errors.py                    ← register_envelope_handler (uniforme cross-service)
│
├── api_gateway/                    (:8000)
│   ├── main.py
│   ├── clients/{identity,patient,inventory,prescription}.py
│   └── routers/{auth,dashboards,proxy}.py
│
├── identity_service/               (:8001)
│   ├── main.py · schemas.py · seed.py · security.py
│   └── routers/auth.py
│
├── patient_service/                (:8002)
│   ├── main.py · schemas.py · seed.py
│   ├── clients/prescription.py     ← para GET /patients/{id}/history
│   └── routers/patients.py
│
├── inventory_service/              (:8003)
│   ├── main.py · schemas.py · seed.py
│   └── routers/{medications,batches,writeoffs}.py
│
├── prescription_service/           (:8004) ← orquestador central
│   ├── main.py · schemas.py · seed.py
│   ├── clients/{patient,inventory,notification}.py
│   └── routers/prescriptions.py
│
├── notification_service/           (:8005)
│   ├── main.py · schemas.py · seed.py
│   ├── providers.py                ← Twilio + SendGrid adapter stubs
│   └── routers/notifications.py
│
└── report_service/                 (:8006)
    ├── main.py
    ├── clients/{inventory,prescription}.py
    └── routers/{reports,analytics}.py
```

> Cada servicio de dominio incluye además `db.py` (engine + `SessionLocal`) y `models.py`
> (modelos SQLAlchemy 2.0). La persistencia es **PostgreSQL, una base por servicio**.

---

## 2. Stack tecnológico

| Capa | Herramienta | Versión | Para qué se usa |
|------|------------|---------|-----------------|
| Lenguaje | **Python** | 3.12 (modo Docker) o 3.11/3.12 (modo local) | Lenguaje de implementación de los 7 servicios |
| Framework web | **FastAPI** | 0.115.0 | Routing, validación, generación automática de OpenAPI/Swagger UI |
| Servidor ASGI | **uvicorn[standard]** | 0.32.0 | Servidor de aplicación (con websockets + http extras) |
| Validación / DTOs | **Pydantic** | 2.9.2 | Schemas tipados, parsing y serialización JSON |
| Cliente HTTP | **httpx** | 0.27.2 | Llamadas inter-servicio sincrónicas (clientes que un servicio usa para hablarle a otro) |
| Retry policy | **tenacity** | 8.5.0 | Decoradores declarativos para retry con backoff exponencial |
| Persistencia | **PostgreSQL** | 16 | Base de datos por servicio (Database per Service) |
| ORM | **SQLAlchemy** | 2.0.35 | Modelos y consultas (síncrono); invariante de stock con `SELECT FOR UPDATE` |
| Driver DB | **psycopg2-binary** | 2.9.9 | Conector PostgreSQL |
| Tests | **pytest** | 8.3.3 | Suite de integración cross-service |
| Contenedores | **Docker Desktop** | 24+ (Compose v2) | Orquestación de 8 containers (7 servicios + PostgreSQL) |

---

## 3. Servicios - URL, puerto y responsabilidad

| Servicio                | URL local                 | Swagger UI                 | Responsabilidad                                              | Tag en OpenAPI                          |
| ----------------------- | ------------------------- | -------------------------- | ------------------------------------------------------------ | --------------------------------------- |
| **ApiGateway**          | http://localhost:**8000** | http://localhost:8000/docs | Entrypoint del frontend. Login passthrough + agregadores BFF | Autenticación (Gateway), Tableros (BFF) |
| **IdentityService**     | http://localhost:**8001** | http://localhost:8001/docs | Autenticación de usuarios del sistema                        | Autenticación                           |
| **PatientService**      | http://localhost:**8002** | http://localhost:8002/docs | Pacientes, apoderados, historial médico                      | Pacientes                               |
| **InventoryService**    | http://localhost:**8003** | http://localhost:8003/docs | Medicamentos, partidas, stock, bajas                         | Medicamentos, Partidas, Bajas           |
| **PrescriptionService** | http://localhost:**8004** | http://localhost:8004/docs | Recetas + máquina de estados                                 | Recetas                                 |
| **NotificationService** | http://localhost:**8005** | http://localhost:8005/docs | SMS / email (Twilio + SendGrid stubs)                        | Notificaciones                          |
| **ReportService**       | http://localhost:**8006** | http://localhost:8006/docs | Informes CSV y analítica agregada                            | Informes, Analítica                     |

Cada servicio tiene además:
- `GET /` - info básica del servicio
- `GET /health` - health check (no en Swagger)
- `GET /openapi.json` - spec OpenAPI cruda

---

## 4. Relaciones inter-servicio

| Endpoint llamado | Servicio dueño | Servicios que invoca internamente (HTTP) |
|-----------------|----------------|------------------------------------------|
| `POST /api/v1/auth/login` (gateway) | ApiGateway | IdentityService |
| `GET /api/v1/doctor/dashboard` (gateway) | ApiGateway | PrescriptionService + PatientService |
| `GET /api/v1/pharmacy/dashboard` (gateway) | ApiGateway | PrescriptionService + InventoryService |
| `GET /api/v1/patients/{id}/history` | PatientService | PrescriptionService |
| `POST /api/v1/prescriptions` (crear) | PrescriptionService | PatientService (valida que el paciente exista) |
| `POST /api/v1/prescriptions/{id}/prepare` | PrescriptionService | InventoryService (reserveStock por línea) |
| `POST /api/v1/prescriptions/{id}/mark-available` | PrescriptionService | InventoryService (reserve) + PatientService (contacto) + NotificationService (correo y SMS, con fallback al apoderado) |
| `POST /api/v1/prescriptions/{id}/cancel` | PrescriptionService | InventoryService (releaseStock si estaba reservado) |
| `POST /api/v1/prescriptions/{id}/deliver` | PrescriptionService | PatientService (valida el apoderado) + InventoryService (consume validando partidas contra lo recetado) |
| `GET /api/v1/prescriptions` y `/queue` | PrescriptionService | Al pasar: expira recetas vencidas (release en InventoryService) y emite recordatorios de retiro (NotificationService) |
| `POST /api/v1/reports` (STOCK/RESERVED/EXPIRED) y `GET /api/v1/analytics/prescription-trend` | ReportService | InventoryService + PrescriptionService |
| El resto (CRUDs simples) | — | Sin cross-service |

**Toda llamada inter-servicio pasa por** `shared/http_client.py` → retry 3× con backoff exponencial + Circuit Breaker (abre tras 5 fallos, reset a los 30s).

---

## 5. Requisitos previos

### Modo Docker (recomendado)

| Herramienta | Versión | Verificar | Instalar |
|-------------|---------|-----------|----------|
| **Docker Desktop** | 24+ (Compose v2) | `docker --version && docker compose version` | https://www.docker.com/products/docker-desktop |
| Espacio en disco | ~500 MB | — | — |
| RAM | ~1 GB | — | — |
| Puertos libres | 8000-8006 | `lsof -i:8000` (vacío = libre) | — |

### Modo SIN Docker (alternativa)

| Herramienta | Versión | Verificar |
|-------------|---------|-----------|
| **Python** | 3.11 o 3.12 (evitar 3.13 por warnings cosméticos de hashlib) | `python3 --version` |
| pip | viene con Python | `pip --version` |

---

## 6. Instalación y ejecución con Docker (recomendado)

Tres comandos cubren el ciclo completo:

```bash
cd backend-microservices
chmod +x *.sh          # solo primera vez en macOS/Linux
./install.sh           # build de las 7 imágenes (~2 min primera vez)
./run.sh               # arranca los 8 containers en background, muestra URLs
```

Para Windows, los mismos pasos pero con archivos `.bat`:

```cmd
install.bat
run.bat
```

Tras `run.sh` / `run.bat`, abrir en el navegador: **http://localhost:8000/docs**

### Para detener

```bash
./stop.sh              # o stop.bat en Windows
```

### Para resetear los datos a la seed inicial

La persistencia es PostgreSQL: `down` + `up` **conserva** los datos. Para volver al seed hay
que borrar el volumen:

```bash
docker compose down -v && ./run.sh   # -v borra el volumen de Postgres; al re-arrancar se siembra de nuevo
```

---

## 7. Scripts disponibles

### Modo Docker

| Script                       | Qué hace                                                                                                                                                                                         | Cuándo usarlo                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| `install.sh` / `install.bat` | Verifica que Docker está corriendo. Ejecuta `docker compose build` para construir las 7 imágenes a partir del Dockerfile compartido.                                                             | **Una sola vez** tras clonar el repo, o cuando cambia código. |
| `run.sh` / `run.bat`         | Verifica Docker activo. Ejecuta `docker compose up -d` para arrancar los 8 containers en background. Espera unos segundos a que estén healthy. Imprime el estado y todas las URLs de Swagger UI. | Cada vez que quieres arrancar el sandbox.                     |
| `stop.sh` / `stop.bat`       | Ejecuta `docker compose down`, detiene y elimina los 8 containers + la red Docker. **Las imágenes permanecen** (próxima vez `run.sh` es rápido).                                                 | Cuando terminas de trabajar.                                  |

### Modo SIN Docker

| Script                                   | Qué hace                                                                                                                                                                                        | Cuándo usarlo                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `install-local.sh` / `install-local.bat` | Verifica Python instalado. Crea `.venv/` y ejecuta `pip install -r requirements.txt`.                                                                                                           | Una vez en máquinas sin Docker.    |
| `run-local.sh`                           | Setea env vars `*_SERVICE_URL=http://localhost:XXXX`. Arranca los 7 servicios con `uvicorn` en background. Guarda PIDs en `.pids/` y logs en `logs/<servicio>.log`. Hace health-check de los 7. | Para arrancar sin Docker.          |
| `run-local.bat`                          | Equivalente para Windows: abre 7 ventanas de `cmd`, una por servicio. Cada ventana muestra logs en vivo de ese servicio.                                                                        | Arrancar sin Docker en Windows.    |
| `stop-local.sh`                          | Lee `.pids/*.pid` y mata los procesos. Borra `.pids/`.                                                                                                                                          | Detener modo local en macOS/Linux. |
| `stop-local.bat`                         | Mata los procesos que escuchan en los puertos 8000-8006.                                                                                                                                        | Detener modo local en Windows.     |

---

## 8. Ejecución sin Docker (alternativa)

Pre-requisito: Python 3.11 o 3.12 instalado y disponible en `PATH`.

### macOS / Linux

```bash
chmod +x *.sh                # solo primera vez
./install-local.sh           # crea .venv + pip install
./run-local.sh               # arranca los 7 servicios en background
./stop-local.sh              # detener todo
```

### Windows

```cmd
install-local.bat            REM crea .venv + pip install
run-local.bat                REM abre 7 ventanas cmd, una por servicio
stop-local.bat               REM mata los procesos por puerto
```

Los logs en macOS/Linux quedan en `./logs/<servicio>.log`. En Windows aparecen en cada ventana de cmd.

---

## 9. Usuarios de demostración

El login valida usuario y contraseña contra IdentityService; credenciales inválidas devuelven 401. El token emitido sigue siendo un stub de sandbox (`sandbox-token-USR-XXX`), que es lo que los demás servicios usan para resolver la identidad y el rol.

### Login y token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"drperez","password":"medico2026"}'
```

Devuelve:

```json
{
  "statusCode": 200,
  "data": {
    "token": "sandbox-token-USR-001",
    "user": {
      "id": "USR-001",
      "username": "drperez",
      "rut": "11.111.111-1",
      "fullName": "Dr. Juan Pérez",
      "email": "juan.perez@cesfam.cl",
      "role": "doctor"
    }
  }, ...
}
```

### Credenciales de demostración

| username    | password       | Token resultante        | Usuario        | Rol                | Para probar                                              |
| ----------- | -------------- | ----------------------- | -------------- | ------------------ | -------------------------------------------------------- |
| `drperez`   | `medico2026`   | `sandbox-token-USR-001` | Dr. Juan Pérez | **doctor**         | Flujos médicos: crear recetas, ver historial paciente    |
| `dralopez`  | `medico2026`   | `sandbox-token-USR-003` | Dra. Ana López | **doctor**         | Médico alternativo                                       |
| `mgonzalez` | `farmacia2026` | `sandbox-token-USR-002` | María González | **pharmacy_staff** | Flujos farmacia: preparar, entregar, write-offs, reports |

Las mutaciones exigen el rol correspondiente: el **médico** emite recetas y el **personal
de farmacia** prepara, entrega, gestiona stock, bajas y apoderados; con el rol equivocado la
API responde 403. Anular recetas lo pueden hacer ambos.

### Cómo usar el token

Una vez iniciada la sesión, el token va en el encabezado `Authorization`:

```bash
curl http://localhost:8000/api/v1/doctor/dashboard \
  -H "Authorization: Bearer sandbox-token-USR-001"
```

En **Swagger UI**, (recomendado para explorar):
1. Haz clic en el botón **Authorize** (arriba a la derecha de la página).
2. Pegar el token, (por ejemplo: `sandbox-token-USR-002`) **sin** el prefijo "Bearer".
3. Ahora cualquier endpoint que ejecutes incluye el header automáticamente

### Validar identidad propagada

```bash
# Login como pharmacy_staff
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"mgonzalez","password":"farmacia2026"}'
# → token sandbox-token-USR-002

# Verificar que /me retorna pharmacy_staff (no default doctor)
curl http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer sandbox-token-USR-002"
# → role: "pharmacy_staff"
```

---

## 10. Datos iniciales (seed)

Cada servicio siembra su base al arrancar (PostgreSQL, una base por servicio). El seed es **idempotente**: solo corre si las tablas están vacías.

| Servicio             | Qué hay precargado                                                                                                                                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| identity_service     | **3 usuarios**                                                                                                                                                                                                                              |
| patient_service      | **5 pacientes** (PAT-001 a PAT-005) + **2 apoderados** (GRD-001 hijo, GRD-002 esposo, ambos asociados a PAT-001)                                                                                                                            |
| inventory_service    | **14 medicamentos** (MED-0001 a MED-0014: Paracetamol, Ibuprofeno, Amoxicilina, Omeprazol, Enalapril, Aspirina, Losartán, Metformina, Atorvastatina, Amlodipino, Levotiroxina, Hidroclorotiazida, Sertralina, Furosemida) + **14 partidas** (BCH-001 a BCH-014) + **2 bajas** (WOF-001, WOF-002), con el invariante de stock respetado |
| prescription_service | **15 recetas** en distintos estados (R001-R004, R012, R045, R050-R058)                                                                                                                                                                                  |
| notification_service | **1 notificación histórica** (NTF-001)                                                                                                                                                                                                      |
| report_service       | Sin estado, los reportes se generan on-demand                                                                                                                                                                                               |

---

## 11. Cómo probar el sandbox

### Flujo recomendado para entender la arquitectura

```bash
TOKEN_MEDICO="Bearer sandbox-token-USR-001"      # drperez: emite recetas
TOKEN_FARMACIA="Bearer sandbox-token-USR-002"    # mgonzalez: prepara y entrega

# 1) Login (passthrough gateway → identity)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" -d '{"username":"drperez","password":"medico2026"}'

# 2) Dashboard del médico (1 call → 3 servicios)
curl http://localhost:8000/api/v1/doctor/dashboard -H "Authorization: $TOKEN_MEDICO"

# 3) Historial de un paciente (1 call → 2 servicios)
curl http://localhost:8002/api/v1/patients/PAT-001/history -H "Authorization: $TOKEN_MEDICO"

# 4) Crear receta como médico (valida paciente cross-service; usar una fecha límite futura)
curl -X POST http://localhost:8004/api/v1/prescriptions \
  -H "Authorization: $TOKEN_MEDICO" -H "Content-Type: application/json" \
  -d '{"patientId":"PAT-002","treatmentType":"SHORT","durationDays":7,
       "pickupDeadline":"2026-08-15",
       "items":[{"medicationId":"MED-0001","dosesPerInterval":1,"intervalHours":8,
                 "doseDescription":"1 c/8h","durationDays":7,"totalQuantity":10}]}'

# 5) Preparar receta como farmacia (reserva stock cross-service; con rol de médico responde 403)
curl -X POST http://localhost:8004/api/v1/prescriptions/R059/prepare -H "Authorization: $TOKEN_FARMACIA"

# 6) Verificar stock cambió en otro servicio
curl http://localhost:8003/api/v1/medications/MED-0001 -H "Authorization: $TOKEN_MEDICO"
```

### Verificación manual mínima

Con el sandbox corriendo (`./run.sh`):

```bash
# Health check de los 7 servicios
for port in 8000 8001 8002 8003 8004 8005 8006; do
  echo -n "$port: "; curl -s http://localhost:$port/health
  echo
done
# → cada uno debe retornar {"status":"ok","service":"..."}

# Login + verificación de identidad
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"drperez","password":"medico2026"}'
# → ApiResponse con token sandbox-token-USR-001

# Cross-service flow completo: ver el §10 anterior
```
