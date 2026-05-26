# Backend Sandbox — Microservicios

**Resumen**
- El código está dividido por servicio bajo `services/<svc>/`.
- Cada servicio es autónomo y contiene, como mínimo:
  - `services/<svc>/main.py` — entrada FastAPI (uvicorn)
  - `services/<svc>/routers/` — rutas específicas del servicio
  - `services/<svc>/schemas/` — Pydantic schemas locales
- Código compartido: `services/common/` (DB, modelos, enums, deps).

Estructura ejemplo

- `services/auth/` → `main.py`, `routers/auth.py`, `schemas/*`
- `services/patients/` → `main.py`, `routers/patients.py`, `schemas/*`
- `services/medications/` → `main.py`, `routers/medications.py`, `schemas/*`
- `services/prescriptions/` → `main.py`, `routers/prescriptions.py`, `schemas/*`
- `services/reports/` → `main.py`, `routers/reports.py`, `schemas/*`
- `services/inventory/` → `routers/batches.py`, `routers/writeoffs.py`, `schemas/inventory.py`
- `services/common/` → `db.py`, `models.py`, `enums.py`, `deps.py`

Puertos por defecto (docker-compose)
- `auth`         → 8001
- `patients`     → 8002
- `medications`  → 8003
- `prescriptions`→ 8004
- `reports`      → 8005

Todos los servicios escuchan internamente en `:8000`.

Dependencias y requerimientos
- Las dependencias principales están en `requirements.txt`.


Arrancar localmente (entorno virtual)

```bash
cd backend-sandbox
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --port 8000 --reload
```

Arrancar un solo servicio en desarrollo

```bash
# desde la raíz del repo
uvicorn services.auth.main:app --host 0.0.0.0 --port 8000 --reload
# o para patients
uvicorn services.patients.main:app --host 0.0.0.0 --port 8000 --reload
```

Arrancar la suite con Docker Compose

```bash
docker compose up -d --build
```

- Compose construye una sola imagen del proyecto y lanza múltiples contenedores que ejecutan distintos entrypoints (`services.<svc>.main:app`).
- `DATABASE_URL` se inyecta desde `docker-compose.yml` apuntando al servicio `db`.


