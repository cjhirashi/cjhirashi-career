# ADR-029: Harness de agentes fuera de la API (`cjhirashi-career-ai`) y sin indexación

## Estado

Aceptado — 2026-10-13 (aprobado por el usuario en el Gate 2 de la feature 009, junto con
la enmienda de la Constitución Art. 2 y 4). Revisa parcialmente el ADR-025 y las
specs 001–005.

## Contexto

La API de carrera mezcla el CRUD de datos con el harness de agentes sobre AWS Bedrock
(bucle, perfiles, tools, delegación, memoria, costes, imágenes) y una base de conocimiento
vectorial (Qdrant) alimentada en cada escritura. La indexación gasta embeddings sin
consumidor real y el harness acopla la API a un proveedor concreto. Existe un andamiaje
`cjhirashi-career-ai` ignorado por git, sin tests.

## Decisión

Decisiones D-01..D-22 de la spec 009 (todas del usuario; D-15..D-22 en la Fase 2):

- El harness completo se traslada a `cjhirashi-career-ai`, versionado en el monorepo, con
  BD propia (`career_ai_db`), Alembic propio y una interfaz de proveedor de modelos
  (Bedrock como única implementación; sólo ésta importa el SDK de AWS).
- El harness accede a los datos de carrera, metodologías, secciones y archivos sólo por la
  API REST, con el JWT del usuario (cuenta de servicio con rol propio `service` y lista explícita de rutas para tareas programadas, D-17; el JWT lleva un claim `role`, D-18).
- El Admin llama al harness directamente bajo `/ai/` (mismo dominio, SSE), con paridad
  exacta del contrato `/bedrock/*` y `/agent-tasks/*`.
- La memoria del agente pasa a Postgres del harness con búsqueda de texto completo y su contenido se migra desde Qdrant (D-15); `search_knowledge_base`, `reindex` y `knowledge/search` se retiran (D-16).
- `audit_logs` se queda en la API con endpoints REST (D-19); se añade `POST /notifications` solo para `service` (D-20). La BD del harness es `career_ai_db` en `postgres_db` con usuario propio (D-21).
- Se elimina la indexación, la KB y Qdrant. La API queda como servicio de datos puro y los
  tokens `agent` quedan limitados a `/career/*`.
- Corte en tres etapas reversibles; las 11 tablas `bedrock_*` se copian y luego se eliminan
  de `career_db` con una migración que exige verificación previa.

## Qué reemplaza parcialmente

- **ADR-025** (generación de imágenes con Stability): la implementación pasa al provider
  Bedrock del harness; la decisión de modelo se mantiene.
- **Specs 001–005** (agentes y metodologías por sección): el harness sale de la API; las
  metodologías y secciones siguen en la API (D-10).
- **Constitución, Art. 2 y Art. 4** (enmienda aprobada):
  - Art. 2: `infraestructura` pasa a `[ postgres-compartida (Alembic en api; BD propia career_ai_db del harness), minio ]` (sin `qdrant`); se retira el sustrato `qdrant-vector`; `bedrock-llm` pasa a ser la implementación Bedrock del provider del servicio `ai`.
  - Art. 4: el Alembic de `cjhirashi-career-api` gobierna solo `career_db`; `cjhirashi-career-ai` usa su propia base `career_ai_db` (mismo contenedor `postgres_db`, usuario propio sin permisos sobre `career_db`) con Alembic propio y sesión async (`+asyncpg`).
  - Decisiones adicionales del Gate 2: D-23 (usuario inactivo conserva el chat hasta que caduque el token) y D-24 (full-text `spanish` configurable).

## Alternativas descartadas

Conexión directa del harness a `career_db`; esquema aparte en `career_db`; la API como
proxy; mantener un índice propio en el harness; subdominio propio; repositorio separado;
corte único con ventana de mantenimiento; rediseño neutro de rutas en esta feature.

## Consecuencias

- Una nueva unidad de despliegue, una BD y un secreto JWT compartido.
- Las tools pasan de acceso directo a REST: más latencia; la API gana endpoints aditivos (`/notifications`, `/audit-log`) y el claim `role`.
- La memoria cambia de relevancia vectorial a texto completo; `search_knowledge_base` desaparece.
- El harness no consulta `is_active`: un usuario desactivado conserva el chat hasta que expire su access token (los datos siguen pasando por la API).
- D-17 enmienda D-09/D-14: la cuenta de servicio ya no es un token `agent`.
- La API reduce su superficie y sus dependencias (boto3, qdrant-client).
