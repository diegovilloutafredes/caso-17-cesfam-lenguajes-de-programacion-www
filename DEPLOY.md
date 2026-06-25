# Despliegue (dev/staging)

Arquitectura desplegada: **backend de microservicios** (`backend-microservices/`) en **Railway**
y **frontend** React/Vite (`frontend/`) en **Vercel**. Persistencia PostgreSQL con
**una base por servicio**. Todo dev/staging; nada en producción.

## Forma del despliegue

En Railway todo el backend corre como **un solo servicio** que levanta los **7 procesos
uvicorn** co-locados (`backend-microservices/railway-start.sh`): los 6 servicios de dominio
escuchan en `localhost` y el **ApiGateway** es el único público (`0.0.0.0:$PORT`). Las
llamadas inter-servicio van por HTTP `localhost`, así que no aplica la red privada IPv6 de
Railway. El código y los diagramas siguen siendo 7 microservicios REST + 5 bases separadas;
solo se empaquetan juntos en el deploy.

```
Vercel (React)  ──HTTPS──>  Railway: api_gateway (público)
                                       │  HTTP localhost
                                       ├─ identity_service     :8001 ─┐
                                       ├─ patient_service      :8002  │
                                       ├─ inventory_service    :8003  │  Railway Postgres
                                       ├─ prescription_service :8004  ├─ identity_db / patient_db /
                                       ├─ notification_service :8005  │  inventory_db / prescription_db /
                                       └─ report_service       :8006 ─┘  notification_db (auto-creadas)
```

## 0. Local (Docker)

```bash
cd backend-microservices
docker compose up -d --build      # Postgres + 7 servicios (un contenedor por servicio)
./run-tests.sh                    # 13 tests de integración
./tests/resilience-test.sh        # degradación + circuit breaker (5.4)

cd ../frontend
npm install && npm run dev         # Vite en :5173, consume http://localhost:8000
```

## 1. Backend — Railway (CLI, sin push a GitHub)

Se despliega el código local directo con la CLI; no requiere subir nada al repositorio.
El build (Dockerfile) y el arranque (`sh railway-start.sh`) ya van declarados en
`backend-microservices/railway.json`.

1. Cuenta en [railway.com](https://railway.com), plan **Hobby** ($5/mes) — no el Trial.
   Instalar la CLI: `npm i -g @railway/cli`.
2. `railway login` (abre el navegador con tu cuenta).
3. Desde `backend-microservices/`:
   - `railway init` → crea el proyecto (ej. `cesfam`).
   - `railway add --database postgres` → agrega el Postgres del proyecto.
   - `railway up` → sube el código local, construye con el Dockerfile y arranca los 7
     procesos. Las 5 bases (`identity_db`, …) se crean solas al iniciar.
4. En el servicio del backend, **Variables** (referencian al Postgres del proyecto):

   | Variable | Valor |
   |---|---|
   | `PGHOST` | `${{Postgres.RAILWAY_PRIVATE_DOMAIN}}` |
   | `PGPORT` | `${{Postgres.PGPORT}}` |
   | `PGUSER` | `${{Postgres.PGUSER}}` |
   | `PGPASSWORD` | `${{Postgres.PGPASSWORD}}` |
   | `PGDATABASE` | `${{Postgres.PGDATABASE}}` |
   | `CORS_ORIGINS` | (se completa en el paso 3, con el dominio de Vercel) |

   > Si el servicio Postgres tiene otro nombre, ajustar el prefijo `${{NOMBRE.…}}`.
5. `railway domain` (o Settings → Networking → Generate Domain) → URL pública del gateway:
   `https://<algo>.up.railway.app`. Verificar `…/health` → `{"status":"ok"}`.

> Alternativa con GitHub (cuando se pushee la rama): New Project → Deploy from GitHub repo,
> Root Directory `backend-microservices`, branch `deploy/railway`; el `railway.json` aplica igual.

## 2. Frontend — Vercel

1. Importar el repo en [vercel.com] con **Root Directory = `frontend`** (usa `vercel.json`:
   framework Vite + rewrites SPA).
2. Variable de entorno (build): `VITE_API_URL = https://<algo>.up.railway.app` (la URL del
   gateway de Railway, sin slash final).
3. Deploy → se obtiene el dominio `https://<app>.vercel.app`.

## 3. Conectar CORS

1. En Railway, setear `CORS_ORIGINS = https://<app>.vercel.app` en el servicio del backend
   (varios dominios separados por coma si hay previews) y redeployar.
2. Abrir el frontend en Vercel, iniciar sesión (`drperez` médico / `mgonzalez` farmacia) y
   verificar que el tablero carga datos a través del gateway.

## 4. Cierre del proyecto

El proyecto vive hasta el **8 de julio**. Para no seguir facturando, eliminar el proyecto en
Railway (o pausar los servicios) y el proyecto en Vercel cuando termine la entrega.

## 5. Fallback de grabación

Si el cloud falla durante la grabación: `cd backend-microservices && docker compose up -d` y
`npm --prefix frontend run dev` reproducen todo en local en segundos (frontend → `:8000`).
