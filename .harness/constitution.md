---
titulo: Constitución del arnés — cjhirashi-career
tipo: constitution
estado: approved
fecha: 2026-09-04
metodo: SDD Anchored (versión simplificada)
---

# Constitución — cjhirashi-career

Principios innegociables que toda `spec.md` y todo `plan.md` heredan y respetan. Se
valida **antes** de redactar cada spec. Cambiar un artículo exige un `ADR-`.

Separación estricta: `.harness/` = **cómo trabajamos** · `docs/` = **el producto**.
Al crear un archivo, pregunta cuál de los dos es.

---

## Artículo 1 · Arquitectura

El proyecto sigue el **patrón detectado en la Génesis (modo alineación, 2026-09-04)** —
ver Artículo 2 y `.harness/decisions/ADR-001-adopcion-arnes-sdd-anchored.md`. Todo el
desarrollo es **conforme a ese patrón**; el gate verifica la conformidad. Cambiar de
patrón exige un `ADR-` nuevo.

- **Monorepo de microservicios** (4 servicios + infraestructura compartida).
  El MCP Server se retiró el 2026-09-04 — ver `docs/09-DECISIONS/023-retirar-mcp-server.md`.
- **Patrón interno = por capas.** Servicios Python: `routes → services → repositories
  → models`. Frontends React: `pages/components → hooks → services (API tipada) →
  stores`. La lógica de negocio vive en `services/`, no en `routes/` ni en componentes.
- Nada de dependencias nuevas de terceros sin justificación en un `plan.md`/`ADR-`.

## Artículo 2 · Perfil de arquitectura  *(detectado en la Génesis)*

```yaml
estilo_aplicacion: microservicios-monorepo
patron_interno:    por-capas            # detectado; no hexagonal
patron_interno_adr: ADR-001
servicios:
  cjhirashi-career-api:       { stack: python/fastapi,        tipo: sistema-de-registro }
  cjhirashi-career-ai:        { stack: python/fastapi-async,  tipo: microservicio-IA (AWS Bedrock) }
  cjhirashi-career-admin:     { stack: react/vite (SPA),      tipo: panel de administración }
  cjhirashi-career-portfolio: { stack: react/vite (SPA),      tipo: portal público read-only }
  # cjhirashi-career-mcp retirado 2026-09-04 — ADR-023
infraestructura: [ postgres-compartida (Alembic en api), qdrant, minio ]
topologia_agentes: multi-perfil-bedrock   # perfiles agent-N, delegación entre perfiles, niveles L1/L2/L3 (ADR 012/013)
sustratos_integracion:
  - rest-http            # FastAPI en api/ai; consumido por los frontends
  - bedrock-llm          # servicio ai contra AWS Bedrock Converse API
  - qdrant-vector        # búsqueda semántica
capas_transversales: [ observabilidad (prometheus + logging/tracing), auth-jwt ]
rutas:
  arnes: .harness/
  specs: .harness/specs/
  decisiones: .harness/decisions/
```

## Artículo 3 · Testing

- **TDD en la Fase 4** (test antes que código).
- Cobertura mínima **80 %** por módulo tocado (umbral que el verificador exige);
  **objetivo 90 %** para código nuevo bajo el arnés.
- Pruebas **por capa**: modelo/repositorio (unit) · servicio (unit + dobles) ·
  ruta/endpoint (integración) · flujo (e2e con JWT real).
- **Verificación real, no autoreporte:** el servicio **arranca** (uvicorn / `docker
  compose` → `GET /health`), el endpoint **responde**. Editar un archivo de estado
  **no es verificar**. La evidencia es salida de terminal **pegada**, nunca "esperada".

## Artículo 4 · Persistencia

- **Postgres compartida**, gobernada por Alembic en `cjhirashi-career-api`.
- La dev DB tiene cambios aplicados por `ALTER TABLE` directo → **no asumir** que
  `alembic upgrade head` = estado real del schema. Verificar contra la DB.
- `cjhirashi-career-ai` usa la misma Postgres con **sesión async** (`+asyncpg` en
  `DATABASE_URL`).

## Artículo 5 · Seguridad

- Secretos fuera del repo (`.env` gitignored; ver `docs/ENVIRONMENT-SECURITY.md`).
- Auth por **JWT**; los endpoints de negocio exigen `get_current_user`.
- Llamadas a Bedrock con **coste**: se pide autorización explícita al humano y se
  registra el coste antes de ejecutarlas en una prueba.

## Artículo 6 · Contratos y errores

- APIs REST: contrato en OpenAPI (el que FastAPI expone en `/openapi.json`); si una
  feature ancla un contrato committeado, va en `cjhirashi-career-api/openapi.yaml`.
- Errores de API con formato **Problem Details (RFC 9457)**.
- **Contrato de red con `cjhirashi-srv`: `caddy.json` (raíz).** Editamos sólo el
  bloque `servicios`; el bloque `cjhirashi_srv` lo escribe `cjhirashi-srv` (no tocar).

## Artículo 7 · Observabilidad

- Logging estructurado + correlación de trazas. Métricas Prometheus (`prometheus.yml`).

## Artículo 8 · Gates y aprobaciones

- **Value Captain** y **Tech Lead**: el humano del proyecto (ambos roles). La **IA no
  autoaprueba** PRs ni marca `verified`.
- 2 puntos de aprobación humana: tras **Specify** (Fase 1) y tras **Plan** (Fase 2).

## Artículo 9 · Convenciones

- Idioma: **código y comentarios en inglés**; specs, `.harness/`, ADRs e interacción
  en **español**.
- IDs: `RF-NNN` / `RNF-NNN` (por feature) · `T-NNN` (por feature) · `ADR-NNN` (proyecto).
  Estables, nunca reutilizados; el número se **reserva creando el archivo**.
- Ramas y carpetas de feature: `NNN-slug` en kebab-case, ≤ 5 palabras.
- Commits: **Conventional Commits** + sufijo `(RF-NNN)`.
- Anotación de tests con su `RF-`: pytest `@pytest.mark.requisito("RF-014")` ·
  Vitest `describe("RF-014: …", …)`.

## Artículo 10 · Regla de raíz (prohibido el parche)

- Toda corrección ataca la **causa raíz**, nunca el síntoma. Sin *workarounds*, sin
  código-tirita que enmascare un fallo, sin `TODO`/`FIXME` sin ticket.
- Diferir la causa raíz es válido **sólo** como `RF-`/`RNF-`/`ADR-` explícito en el
  backlog, con justificación — nunca como código que se queda.
- El verificador rechaza la entrega cuya solución no explique y ataque la causa.

## Artículo 11 · Mapa de documentación del proyecto

La doc del producto se degrada si no se mantiene con el código. El arnés la
sincroniza (Fase 2 `plan.md §Impacto en documentación` → tareas `[doc]` → ruta en
`covers` → bloque de gate por obsolescencia).

| Documento | Ruta | Se actualiza cuando cambia… |
|---|---|---|
| arc42 | `docs/01`–`docs/12` | estructura, componentes, decisiones, riesgos, calidad |
| ADRs (índice + decisiones) | `docs/09-DECISIONS/` | una decisión arquitectónica del **producto** |
| Sistema Bedrock | `docs/BEDROCK-SYSTEM.md` | comportamiento del subsistema de agentes / perfiles |
| Setup del panel | `docs/ADMIN_PANEL_SETUP.md` | arranque / configuración del panel admin |
| Entorno y seguridad | `docs/ENVIRONMENT-SECURITY.md` | variables de entorno, secretos, políticas |
| Plan de implementación | `docs/IMPLEMENTATION_PLAN.md` | roadmap / fases del producto |
| Contrato de red | `caddy.json` (bloque `servicios`) | exposición / routing de un servicio |
| README de servicio | `cjhirashi-career-*/README.md` (api: `src/README.md`, `src/models/README.md`) | comandos, setup, superficie pública |
| Compose | `docker-compose.yml` | servicios, puertos, dependencias, healthchecks |

> Las decisiones **del arnés** van en `.harness/decisions/`, no en `docs/09-DECISIONS/`.

## Artículo 12 · Anti-hipersistema

1. **3 archivos por feature** (`spec.md`, `plan.md`, `tasks.md`) + `contracts/` si
   aplica. Añadir un tipo de artefacto exige un `ADR-`.
2. El método vive en **`.harness/method.md`** (1 archivo). No crece sin podar.
3. **Un gate por frontera real.** Nada "por si acaso".
4. **Un canon por hecho.** Cero duplicación entre `AGENTS.md`, esta Constitución y `docs/`.
5. **Estado en disco, no en el chat.** Siempre.
6. **Rúbrica primero.** Lo trivial no toca el arnés.

---

## Hazards conocidos del código (contexto duro — verificar si reaparecen)

- **Reportes "FASE X 100%" sin arranque real.** `cjhirashi-career-ai` estuvo
  "completo" sin poder arrancar. → Art. 3: verificación real obligatoria.
- **`main.py` de `ai` silenciando `ImportError` de routers** y arrancando "sano" sin
  endpoints de negocio. → confirmar que los routers cargan.
- **Stubs falsos en `ai/src/models/`** que sombreaban los modelos reales
  (`from models import *` con `Base` desconectado). → confirmar modelos reales.
- **Secuencias PG desincronizadas** de IDs congelados → 500 al crear grupos/secciones.
- **`DetachedInstanceError`** por cache de proceso con filas ORM vivas fuera de sesión.
- **dev DB no trackea Alembic del todo** (Art. 4).

## Historial de enmiendas

| Fecha | Artículo | Cambio | ADR |
|---|---|---|---|
| 2026-09-04 | — | Constitución inicial (Génesis en modo alineación) | ADR-001 |
| 2026-09-04 | 1, 2, 6 | Retiro del MCP Server: 5→4 servicios; fuera el sustrato `mcp` y la regla de JSON Schema por tool | ADR-023 |
