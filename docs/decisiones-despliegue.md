# Despliegue CESFAM — proceso y decisiones (ambiente de desarrollo)

> Todo el despliegue es de **desarrollo / demo**: nada se promueve a producción. Datos de
> seed, vida corta (hasta el 8 de julio). **Sin pipelines de CI/CD**: el deploy se hace a
> mano con scripts locales (`make deploy-back`, `make deploy-front`).

## Arquitectura desplegada

```
Vercel (React/Vite, preview)  ──HTTPS──>  Railway (1 servicio = 7 procesos uvicorn)
                                              api_gateway (público)
                                                │ HTTP localhost
                                                └─ identity / patient / inventory /
                                                   prescription / notification / report
                                                        │
                                              Railway Postgres (5 bases: Database per Service)
```

El frontend usa **una sola base URL**: el ApiGateway (BFF).

## Paso a paso

### Backend (Railway)
1. **Empaquetado:** un `Dockerfile` copia los 7 servicios; `railway-start.sh` levanta los
   7 procesos uvicorn (6 de dominio en `localhost`, el gateway público en `0.0.0.0:$PORT`)
   y crea las 5 bases si faltan.
2. **`railway.json`:** declara build (Dockerfile) + start (`railway-start.sh`) + healthcheck.
3. **Postgres** gestionado de Railway; las 5 bases (`identity_db`…) se crean al arrancar.
4. **Variables de conexión** por referencia (`${{Postgres.*}}`): las claves viven en Railway.
5. **Deploy:** `railway up` sube el código local (sin push a GitHub).
6. **Dominio** público del gateway + verificación `/health`.

### Frontend (Vercel)
1. Vercel toma `frontend/` (Vite + rewrites SPA de `vercel.json`).
2. `VITE_API_URL` = URL del gateway en Railway (en build).
3. Deploy de **desarrollo (preview)**, no producción.

## Decisiones y trade-offs

| # | Decisión | A favor | En contra / riesgo |
|---|---|---|---|
| D1 | **Railway** para el backend | Always-on por defecto, HTTPS automático, Postgres con varias bases, mínima configuración | Trial con 1 GB RAM y crédito acotado |
| D2 | **5 bases en 1 Postgres** (Database per Service) | Fiel al patrón sin pagar 5 instancias | Comparten instancia (aceptable en dev) |
| D3 | **1 servicio con los 7 procesos** (vs 7 servicios) | Config mínima; esquiva el footgun IPv6 de Railway (uvicorn no hace dual-stack); más barato; dominio de servicios 100% privado | Co-locados (un deploy, destino compartido). El código y los diagramas siguen siendo microservicios |
| D4 | **Partir en Trial** (vs Hobby) | $0, sin tarjeta para probar | 1 GB RAM (7 uvicorn al límite → posible OOM), crédito único de $5, restricciones de red en "Limited Trial" |
| D5 | **Deploy sin push** (`railway up`) | Respeta "no push"; no requiere GitHub | El deploy no se versiona automáticamente |
| D6 | **Sin pipelines, scripts locales** | Simple, sin infraestructura de CI; adecuado para entrega corta | No hay deploy automático por commit (no se necesita) |
| D7 | **Ambiente de desarrollo** | No se promueve nada a producción | Railway nombra el entorno "production" por defecto → se renombra a `develop` en el dashboard |

### Plataformas evaluadas para el backend (D1, descartadas)
- **Render free:** cold start 30-60 s por servicio → cascada que rompe la demo; los servicios de dominio quedan públicos.
- **Fly.io:** sin free tier en 2026; exige varios `fly.toml` y tuning de timeouts.
- **Oracle Always Free:** $0 perpetuo, pero aprovisionar el ARM falla seguido ("out of capacity").
- **VPS (Hetzner):** la más barata robusta (~$5), pero requiere SSH + Caddy + firewall.
- **AWS (lo que usó VaquitaApp):** ECS/Fargate ×7 carísimo; free tier de 1 GB no alcanza; un EC2 que sí, ~$15-30/mes.

## Secretos

- Las **sesiones** de Railway y Vercel viven en `~/.railway` y `~/.vercel`, **fuera del repo**.
- Las **claves** (Postgres) son variables del servicio en Railway, nunca en el código.
- `.gitignore` cubre `.env`, `.env.local`, `.env.*.local`, `.railway/`, `.vercel/`.
- Los scripts de deploy **no** hardcodean tokens: usan la sesión logueada de cada CLI.

## Comandos

| Acción | Comando |
|---|---|
| Todo local (back + front) | `make dev` |
| Solo backend local | `make up` · bajar: `make down` · reset: `make clean` |
| Tests | `make test` · `make test-resilience` |
| Deploy backend a la nube | `make deploy-back` |
| Deploy frontend a la nube | `VITE_API_URL=<url-railway> make deploy-front` |
| Estado en la nube | `make cloud-status` |

## Estado

- **Backend:** desplegado y verificado en Railway (`/health`, login, ambos tableros, proxy,
  las 5 bases creadas, los 7 procesos corriendo).
- **Frontend:** pendiente de desplegar en Vercel.
