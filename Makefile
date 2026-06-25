# CESFAM Caso 17 — atajos de desarrollo y despliegue.
# Backend: microservicios FastAPI + PostgreSQL (docker compose). Frontend: React/Vite.
.PHONY: help setup dev up down clean logs test test-resilience front build deploy-back deploy-front cloud-status stop

COMPOSE := docker compose -f backend-microservices/docker-compose.yml

help:  ## Lista los comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── Local: stack completo ─────────────────────────────────────────
setup:  ## Instala las dependencias del frontend
	npm --prefix frontend install

dev:  ## Levanta TODO en local (backend + frontend) en una terminal
	./scripts/dev.sh

# ── Local: backend (docker compose) ───────────────────────────────
up:  ## Solo backend: 7 servicios + Postgres
	$(COMPOSE) up -d --build

down:  ## Baja el backend (conserva los datos)
	$(COMPOSE) down

clean:  ## Baja el backend y borra los datos (reset total)
	$(COMPOSE) down -v

logs:  ## Sigue los logs del backend
	$(COMPOSE) logs -f

# ── Tests ─────────────────────────────────────────────────────────
test:  ## Suite de integración cross-service (requiere 'make up')
	bash backend-microservices/run-tests.sh

test-resilience:  ## Prueba de resiliencia (circuit breaker)
	bash backend-microservices/tests/resilience-test.sh

# ── Local: frontend ───────────────────────────────────────────────
front:  ## Solo frontend (Vite :5173 -> backend :8000)
	VITE_API_URL=http://localhost:8000 npm --prefix frontend run dev

build:  ## Build de producción del frontend
	npm --prefix frontend run build

# ── Nube: deploy de desarrollo (sin push, sin pipelines) ──────────
deploy-back:  ## Despliega el backend a la nube (Railway)
	./scripts/deploy-backend.sh

deploy-front:  ## Despliega el frontend a la nube (Vercel). Requiere VITE_API_URL
	./scripts/deploy-frontend.sh

cloud-status:  ## Estado del despliegue del backend en Railway
	cd backend-microservices && railway status

# ── Utilidad ──────────────────────────────────────────────────────
stop:  ## Detiene el stack local y libera puertos
	./scripts/stop.sh
