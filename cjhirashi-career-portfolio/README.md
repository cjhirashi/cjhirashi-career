# Portal público — cjhirashi-career

SPA pública de solo lectura (`cjhirashi.com`, puerto host 8003) con el portafolio profesional de Carlos Jiménez Hirashi. Lee de la API (`/api/public/*`), recibe los mensajes del formulario de contacto y envía eventos de analítica. Arquitectura: [`docs/05-BUILDING-BLOCK-VIEW.md`](../docs/05-BUILDING-BLOCK-VIEW.md); arranque: [`docs/SETUP.md`](docs/SETUP.md).

**Última actualización**: 2026-11-05

## Páginas

| Ruta | Página | Contenido |
|---|---|---|
| `/` | HomePage | Presentación, stats, stack técnico, proyectos y publicaciones destacados (`GET /public/home`) |
| `/about` | AboutPage | Sobre mí (`GET /public/about`) |
| `/projects`, `/projects/:slug` | ProjectsPage, ProjectDetailPage | Listado con filtros y detalle de cada proyecto, con Markdown, diagramas Archify incrustados y capturas |
| `/blog`, `/blog/:slug` | BlogPage, BlogPostPage | Publicaciones del blog |
| `/contact` | ContactPage | Formulario de contacto: `POST /public/contact-message` (el mensaje llega al Admin) |
| `/privacy` | PrivacyPage | Aviso de privacidad y borrado de los datos de analítica del visitante (`POST /events/forget`) |
| `*` | NotFoundPage | 404 |

Solo el contenido marcado como publicable sale de la API; no hay autenticación.

## Stack

React 18, TypeScript 5, Vite 5, Tailwind CSS (tema claro/oscuro), React Query 5, Zustand 4, React Router 6 y Vitest + React Testing Library. Node 20.

## Estructura

```
src/
├── pages/        # una por ruta
├── components/   # Layout (Header, Footer) y Common (tarjetas, Markdown, chips de métricas, tema)
├── hooks/        # useHome, useAbout, useProjects, useBlog, useContact, useTracking
├── api/          # client.ts (Axios, base VITE_API_URL) y un módulo por recurso, tracking.ts
├── utils/        # tracker.ts, engagement.ts, metrics.ts, theme.ts
├── stores/       # uiStore (tema)
└── tests/        # pruebas por capa
```

## Analítica

El rastreador (`utils/tracker.ts`, `hooks/useTracking.ts`) envía eventos a `POST /events/track`: visitas, tiempo activo, scroll, enlaces salientes, Web Vitals y UTM, con un identificador de visitante seudónimo. Respeta DNT y GPC, no mide en la página de privacidad tras pedir el borrado y se desactiva con `VITE_TRACKING_ENABLED=false`. La API sesioniza, filtra bots y agrega; el tablero está en el Admin (`/metrics`). Flujo: [`docs/06-RUNTIME-VIEW.md`](../docs/06-RUNTIME-VIEW.md).

## Variables de compilación

| Variable | Uso |
|---|---|
| `VITE_API_URL` | Base de la API (`/api` en todos los entornos; la API recibe las rutas sin el prefijo) |
| `VITE_TRACKING_ENABLED` | `false` desactiva el rastreador |
| `VITE_PORTAL_SITE_KEY` | Clave del sitio para la analítica; el compose la toma de `PORTAL_SITE_KEY` como argumento de build |

## Desarrollo y pruebas

```bash
npm ci
cp .env.example .env
npm run dev                  # Vite en :8000, proxy /api → API (cjhirashi-career-api:8000)
npx vitest run               # pruebas (cobertura mínima 80 %)
npm run type-check && npm run lint
```

## Despliegue

Desde la raíz del repo: `docker compose up -d --build portfolio` (Node 20, `serve -s dist -l 8000`; host 8003). Comprobación: `GET http://localhost:8003/`.

## Calidad

- Capas: `pages/components → hooks → api → stores`.
- Cada prueba anota su requisito (`describe("RF-014: …")`).
- Toda feature de interfaz pasa por el experto UX/UI antes de `verified`; contraste AA en ambos temas.

## Contacto

Carlos Jiménez Hirashi, cjhirashi@gmail.com
