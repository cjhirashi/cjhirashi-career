# ADR-029: Harness de agentes fuera de la API (`cjhirashi-career-ai`) y sin indexación

## Estado

Propuesto — 2026-10-13 (feature 009, Fase 2, incorpora D-15..D-22; pendiente de aprobación del usuario en el
Gate 2). Revisa parcialmente el ADR-025 y las specs 001–005.

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
- Corte en tres etapas reversibles; las 10 tablas `bedrock_*` se copian y luego se eliminan
  de `career_db` con una migración que exige verificación previa.

## Qué reemplaza parcialmente

- **ADR-025** (generación de imágenes con Stability): la implementación pasa al provider
  Bedrock del harness; la decisión de modelo se mantiene.
- **Specs 001–005** (agentes y metodologías por sección): el harness sale de la API; las
  metodologías y secciones siguen en la API (D-10).
- **Constitución, Art. 2 (topología/sustrato) y Art. 4**: el Alembic de `career_db` deja de
  gobernar el harness; Qdrant deja de ser sustrato. Su edición requiere OK del usuario.

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
