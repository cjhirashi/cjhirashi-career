# Admin Panel: arranque y configuración

**Última actualización**: 2026-11-05

Guía de arranque del Admin Panel (`cjhirashi-career-admin`). Para la visión de producto y las pantallas, ver el [README del Admin](../cjhirashi-career-admin/README.md) y [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md).

## Requisitos

- Node 20 y npm.
- La API en marcha (por Docker Compose o local) y un usuario administrador.

## Desarrollo local

```bash
cd cjhirashi-career-admin
npm ci
cp .env.example .env      # VITE_API_BASE_URL=/api (por defecto)
npm run dev               # servidor Vite en el puerto 8000
```

El servidor de desarrollo reenvía `/api/*` a `http://cjhirashi-career-api:8000` quitando el prefijo (`vite.config.ts`); fuera de la red Docker cambia ese `target` por la URL de tu API local (`http://localhost:8000`). Las variables del Admin son solo de compilación (`VITE_API_BASE_URL`, `VITE_APP_NAME`, `VITE_APP_VERSION`, `VITE_LOG_LEVEL`).

## Comandos

| Comando | Para qué |
|---|---|
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | `tsc` + build de producción en `dist/` |
| `npm run preview` | Sirve el build local |
| `npm run type-check` | Comprobación de tipos sin emitir |
| `npm run lint` / `lint:fix` | ESLint (sin avisos permitidos) |
| `npm run format` | Prettier |
| `npm test` / `npx vitest run` | Pruebas con Vitest (modo observación / una pasada) |
| `npm run test:coverage` | Cobertura |

## Docker

Desde la raíz del repo, el servicio `admin` del compose construye la imagen (Node 20, `serve -s dist -l 8000`), publica el puerto host **8002** y depende de `api`:

```bash
docker compose up -d --build admin
curl -s http://localhost:8002/ | head -1     # healthcheck: wget a http://localhost:8000/ dentro del contenedor
```

En producción el SPA se sirve en `admin.cjhirashi.com` y Caddy reenvía `/api/` a la API quitando el prefijo; por eso `VITE_API_BASE_URL=/api` sirve en todos los entornos.

## Estructura

```
src/
├── pages/        # una por pantalla (Dashboard, Metrics, Files, Tasks, Agent*, Settings*, …)
├── components/   # compartidos; section/ (plantilla de tabla), career/, bedrock/, tasks/
├── hooks/        # React Query y lógica de pantalla
├── api/          # cliente Axios tipado + un módulo por dominio
├── stores/       # Zustand (sesión, chat, preferencias)
├── config/       # catálogo de recursos de carrera, perfiles y secciones de chat
├── types/ utils/ # tipos y utilidades
└── tests/        # pruebas transversales (las demás conviven con el código)
```

## Autenticación

1. `POST /auth/login` devuelve un token de acceso (7 días) y uno de refresco (30); el store de sesión los conserva en el cliente.
2. El interceptor de Axios añade `Authorization: Bearer` a cada petición y, ante un 401, intenta `POST /auth/refresh` una vez.
3. Sin sesión válida, `PrivateRoute` redirige a `/login`. Cerrar sesión llama a `POST /auth/logout` y limpia el store.

## Pantallas

Rutas definidas en `src/App.tsx`: `/dashboard`, `/metrics`, `/metrics/settings`, `/search-metrics`, `/job-discovery`, `/files`, `/tasks`, `/career/:resourceKey/:recordSlug?` (recursos de carrera), `/agent/*` (chat, catálogo, instrucciones, herramientas, memoria, tareas, auditoría, métricas, plantillas y estilos de PDF), `/settings/*` (agentes, secciones, prompts, errores), `/profile`, `/change-password` y `/login`. Descripción por área en [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md).

## Pruebas

Vitest + React Testing Library; cada prueba anota su requisito (`describe("RF-014: …")`). Cobertura mínima del 80 % (Constitución). Antes de entregar: `npm run type-check`, `npm run lint` y `npx vitest run`.

## Sistema de diseño

Tailwind con tema claro/oscuro por tokens semánticos y contraste AA ([ADR-028](./09-DECISIONS/028-contraste-tokens-semanticos-admin.md)); el sidebar lo gobierna la sección activa ([ADR-024](./09-DECISIONS/024-sidebar-contextual-por-seccion.md)).
