# Portal público: arranque y configuración

**Última actualización**: 2026-11-05

Guía de arranque de `cjhirashi-career-portfolio`. Visión general y páginas: [README](../README.md).

## Requisitos

Node 20 y npm; la API en marcha para ver contenido real.

## Desarrollo

```bash
cd cjhirashi-career-portfolio
npm ci
cp .env.example .env     # VITE_API_URL=/api, VITE_TRACKING_ENABLED=true, VITE_PORTAL_SITE_KEY=
npm run dev              # http://localhost:8000
```

El servidor de desarrollo reenvía `/api/*` a `http://cjhirashi-career-api:8000` quitando el prefijo (`vite.config.ts`). Fuera de la red Docker cambia ese `target` por tu API local. Deja `VITE_TRACKING_ENABLED=false` si no quieres generar analítica en desarrollo.

## Comandos

`npm run build` (tsc + Vite), `npm run preview`, `npm run type-check`, `npm run lint`, `npm run format`, `npx vitest run`, `npm run test:coverage`.

## Docker

```bash
docker compose up -d --build portfolio      # desde la raíz del repo; host 8003 → 8000
curl -s http://localhost:8003/ | head -1
```

La imagen compila el SPA con `VITE_PORTAL_SITE_KEY` (argumento de build tomado de `PORTAL_SITE_KEY` del `.env` raíz) y lo sirve con `serve`.

## Problemas frecuentes

| Síntoma | Causa y salida |
|---|---|
| Páginas vacías o sin proyectos | La API no responde: `curl http://cjhirashi-career-api:8000/health` desde la red Docker; revisa el proxy de `vite.config.ts` |
| La analítica no llega | `VITE_TRACKING_ENABLED` en `false`, DNT/GPC activos o falta `VITE_PORTAL_SITE_KEY` |
| El formulario de contacto devuelve 429 | Límite de 3 mensajes por hora por IP y por correo |
| Puerto 8000 ocupado | `lsof -i :8000` o `npm run dev -- --port 3000` |
