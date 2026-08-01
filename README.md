# Heladería ERP

Monorepo del registro de ventas. `apps/web` contiene el frontend Next.js y
`apps/api` el backend FastAPI. Ambos se despliegan como proyectos Vercel
independientes; el navegador consume exclusivamente rutas same-origin `/api/*`.

## Desarrollo

1. Copiar `.env.example` a `.env`.
2. Iniciar PostgreSQL 17 con `docker compose up -d db`.
3. En `apps/api`, instalar el proyecto y ejecutar `alembic upgrade head`.
4. Provisionar la cuenta con `python -m app.provision usuario`.
5. Ejecutar FastAPI con `uvicorn app.main:app --reload`.
6. En `apps/web`, ejecutar `npm install && npm run dev`.

## Verificación

- Backend: `docker compose run --rm api-tests`
- Frontend: `npm test`, `npm run typecheck` y `npm run test:e2e`

