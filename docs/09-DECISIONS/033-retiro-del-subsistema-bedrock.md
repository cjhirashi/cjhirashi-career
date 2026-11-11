# ADR-033: Se retira el subsistema Bedrock y el catálogo de agentes

## Estado

Aceptado — 2026-11-11 (orden del propietario). Ejecuta lo que el [ADR-032](032-agentes-externos-y-bedrock-fuera-de-operacion.md) dejó pendiente («retirarlo requiere una spec propia»): el propietario pidió el retiro directo.

## Decisión

Los agentes de IA son externos y entran por la API con el rol `agent` (`/career/*` y subida de archivos). Se elimina todo lo que servía a un harness interno:

- **API:** rutas `/bedrock/*` y `/admin-sections`, servicios `bedrock/` y `bedrock_service`, catálogo de secciones y de agentes, asignación de metodologías a agentes, planificador de tareas de agente, generación de imágenes con Stability, y `boto3`.
- **Datos (migración `8d4f2a6c1e93`):** se borran las tablas `bedrock_*` del harness y `admin_section_overrides`, y las columnas `agent_profile_ids` y `section_ids` de `operational_methodologies`. Se conservan `bedrock_tasks` (el tablero de tareas, ahora solo del usuario, bajo `/agent-tasks`) y `audit_logs`.
- **Admin:** páginas de chat, catálogo de agentes, secciones, prompts globales, memoria, instrucciones, herramientas, bitácora y costo; el panel lateral de asistencia; los campos de agente del formulario de tareas y la acción «ejecutar».
- **Código fuera de la API:** `cjhirashi-career-ai` (nunca desplegado) y su spec 009, que queda como registro histórico.
- **Configuración:** `AWS_*` y `BEDROCK_*` salen del entorno y del compose. Qdrant ya se había retirado el mismo día.

## Reversa

Respaldo previo (pg_dump de las tablas retiradas) y imágenes `pre-sin-bedrock`. La migración no tiene vuelta atrás automática.

## Consecuencias

- La documentación del subsistema (`BEDROCK-SYSTEM.md`, `BEDROCK-HARNESS.md`, sección `bedrock`) se elimina; los ADR 008, 012, 013, 019, 022, 025 y 026 quedan como historia del diseño anterior.
- Una auditoría de escrituras de agentes externos y un nuevo arnés propio, si se quisieran, serían trabajo nuevo con su propia spec.
