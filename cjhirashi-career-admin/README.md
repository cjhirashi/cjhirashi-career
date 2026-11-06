# Admin Panel — cjhirashi-career

SPA privada (`admin.cjhirashi.com`, puerto host 8002) con la que Carlos gestiona su carrera, los agentes de IA y la analítica del portafolio. Habla solo con la API REST (`/api/`). Arranque y comandos: [`docs/ADMIN_PANEL_SETUP.md`](../docs/ADMIN_PANEL_SETUP.md); arquitectura: [`docs/05-BUILDING-BLOCK-VIEW.md`](../docs/05-BUILDING-BLOCK-VIEW.md).

**Última actualización**: 2026-11-05

## Qué incluye

- **Panel y métricas**: dashboard, métricas de búsqueda (`/search-metrics`) y tablero de analítica del portafolio (`/metrics`, ver abajo).
- **Carrera**: vista genérica por recurso (`/career/:resourceKey/:recordSlug?`: identidad, competencias, evidencia, vacantes, aplicaciones, contactos, entrevistas, CVs, cartas…), descubrimiento de vacantes (`/job-discovery`) y archivos (`/files`).
- **Tareas** (`/tasks`): lista, kanban, calendario y Gantt; subtareas con turno y tareas programadas para agentes.
- **Agentes**: chat con el orquestador y chat contextual por sección, catálogo, instrucciones, herramientas, memoria, tareas, auditoría, métricas de uso y plantillas y estilos de PDF (`/agent/*`).
- **Configuración**: perfiles de agentes, secciones del Admin, prompts globales y registro de errores (`/settings/*`).
- **Notificaciones**: campana con turnos de tareas y mensajes de contacto del portal.

## Stack

React 18, TypeScript 5, Vite 5, Tailwind CSS (tema claro/oscuro con tokens semánticos), React Query 5, Zustand 4, React Router 6, Axios, Recharts y Vitest + React Testing Library. Node 20.

## Estructura

```
src/
├── pages/        # una página por pantalla (Dashboard, Metrics, PortalSettings, Files, Tasks, Agent*, …)
├── components/   # Layout, Sidebar, Navbar, campana, selectores temáticos; section/ (plantilla de tabla),
│                 # career/ (formularios y vistas de recursos; career/portal/ = tablero), bedrock/ (chat), tasks/
├── hooks/        # useAuth, useCareerResource, useBedrockChat, usePortalAnalytics (un hook por endpoint), …
├── api/          # client.ts (Axios con interceptores JWT) y un módulo por dominio
├── stores/       # authStore, bedrockChatStore, preferencias
├── config/       # careerResources.ts (catálogo de recursos), perfiles y secciones de chat
├── types/ utils/ # tipos y utilidades
└── tests/        # pruebas transversales; el resto conviven con el código
```

## Tablero de métricas del portafolio (`/metrics`)

Lee `/career/portal-metrics/*` (SPEC-0010). Arranca en los últimos 30 días, sin comparar, con **bots y mis visitas excluidos**.

- **Controles:** rango (7/30/90 días o fechas exactas), comparación (periodo anterior, año anterior, mismos días de la semana), filtros combinables (canal, país, dispositivo) y los interruptores de exclusión. Las listas de filtros se piden sin filtros para que elegir uno no vacíe las demás.
- **Arriba:** KPIs con cambio contra el periodo comparado (en el rebote bajar es mejorar), minigráfica y «visitantes ahora» (se actualiza cada 20 s; el resto cada minuto).
- **Gráfica:** visitas por día con el tramo en curso punteado, el periodo comparado y las anotaciones.
- **Paneles:** desglose por pestañas (fuentes, páginas, ubicación con mapa, dispositivos; cada pestaña pide sus datos solo al abrirse), metas y embudo, recorridos y retención semanal, y calidad de los datos (muestra, porcentaje de bots y aviso si hay pocas visitas).
- **Configuración (`/metrics/settings`, enlazada desde el tablero):** crea, edita y elimina metas, embudos y anotaciones. El usuario escribe valores simples (ruta, texto, segundos) y `configModel.ts` los traduce al diccionario `match` del servidor y los valida (un embudo necesita nombre y al menos 2 pasos). Al guardar se invalidan las consultas del tablero, que de otro modo mostraría la versión anterior hasta 5 minutos.
- **Pruebas:** `src/tests/pages/MetricsPage.test.tsx`, `src/tests/api/portalAnalytics.test.ts`, `src/tests/components/portal/format.test.ts`, `src/tests/pages/PortalSettingsPage.test.tsx`, `src/tests/components/portal/configModel.test.ts`, `src/tests/hooks/useCareerMutationsPortal.test.tsx`.

## Desarrollo, pruebas y despliegue

```bash
npm ci
cp .env.example .env          # VITE_API_BASE_URL=/api
npm run dev                   # Vite en :8000 con proxy /api → API
npx vitest run                # pruebas (cobertura mínima 80 %)
npm run type-check && npm run lint
```

- **Docker**: desde la raíz del repo, `docker compose up -d --build admin` (imagen Node 20 que sirve `dist/` con `serve` en el 8000; host 8002).
- **API**: todas las llamadas van a `VITE_API_BASE_URL` (`/api`); Caddy lo reenvía a `cjhirashi-career-api:8000` quitando el prefijo. No hay prefijo `/api/v1`.
- **Autenticación**: `POST /auth/login` → tokens de acceso (7 días) y refresco (30); el interceptor de Axios añade `Authorization: Bearer` y renueva con `/auth/refresh` ante un 401.
- **Guía completa**: [`docs/ADMIN_PANEL_SETUP.md`](../docs/ADMIN_PANEL_SETUP.md). Chat de agentes: [`docs/BEDROCK-CHAT.md`](docs/BEDROCK-CHAT.md).

## Calidad

- Capas del frontend: `pages/components → hooks → api → stores`; la lógica de negocio no vive en los componentes.
- TypeScript estricto, ESLint sin avisos y Prettier.
- Cada prueba anota su requisito (`describe("RF-014: …")`); toda feature de interfaz pasa por el experto UX/UI antes de `verified`.
- Accesibilidad: contraste AA en ambos temas ([ADR-028](../docs/09-DECISIONS/028-contraste-tokens-semanticos-admin.md)).

## Solución de problemas

| Síntoma | Causa y salida |
|---|---|
| La SPA no alcanza la API en desarrollo | El proxy de `vite.config.ts` apunta a `http://cjhirashi-career-api:8000` (red Docker); fuera de Docker cámbialo por tu API local |
| 401 en bucle | Token vencido y refresco inválido: cierra sesión y vuelve a entrar |
| Puerto 8000 ocupado | `lsof -i :8000` y detén el proceso, o `npm run dev -- --port 3000` |
| Pruebas con estado raro | `rm -rf node_modules/.vite coverage && npx vitest run` |

## Contacto

Carlos Jiménez Hirashi, cjhirashi@gmail.com
