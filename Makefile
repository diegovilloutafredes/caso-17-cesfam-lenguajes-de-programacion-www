.PHONY: help setup dev up down clean logs test test-resilience front build deploy-back deploy-front cloud-status reset-cloud-db stop

COMPOSE := docker compose -f backend-microservices/docker-compose.yml

help:  ## Lista los comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup:  ## Instala las dependencias del frontend
	npm --prefix frontend install

dev:  ## Levanta backend y frontend en una terminal
	./scripts/dev.sh

up:  ## Solo backend: 7 servicios + Postgres
	$(COMPOSE) up -d --build

down:  ## Baja el backend (conserva los datos)
	$(COMPOSE) down

clean:  ## Baja el backend y borra los datos (reset total)
	$(COMPOSE) down -v

logs:  ## Sigue los logs del backend
	$(COMPOSE) logs -f

test:  ## Suite de integración cross-service (requiere 'make up')
	bash backend-microservices/run-tests.sh

test-resilience:  ## Prueba de resiliencia (circuit breaker)
	bash backend-microservices/tests/resilience-test.sh

front:  ## Solo frontend (Vite :5173)
	VITE_API_URL=http://localhost:8000 npm --prefix frontend run dev

build:  ## Build de producción del frontend
	npm --prefix frontend run build

# deploy manual, sin pipelines
deploy-back:  ## Despliega el backend a la nube (Railway)
	./scripts/deploy-backend.sh

deploy-front:  ## Despliega el frontend a la nube (Vercel). Requiere VITE_API_URL
	./scripts/deploy-frontend.sh

cloud-status:  ## Estado del despliegue del backend en Railway
	cd backend-microservices && railway status

reset-cloud-db:  ## Resetea las bases de la nube para re-aplicar el seed (destructivo)
	./scripts/reset-cloud-db.sh

stop:  ## Detiene el stack local y libera puertos
	./scripts/stop.sh
