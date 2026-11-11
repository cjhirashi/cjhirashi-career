# ADR-032: Agentes externos por la API; el subsistema Bedrock queda fuera de operación

## Estado

Aceptado — 2026-11-10 (decisión del propietario). Aplaza el ADR-029 y revisa parcialmente los ADR-008, ADR-012, ADR-019, ADR-022 y ADR-026.

## Contexto

El subsistema de agentes sobre AWS Bedrock (orquestador, especialistas, herramientas, memoria, presupuesto) no funcionaba del todo bien. Al propietario le resultó más útil conectar sus propios agentes desde fuera, por la API REST, con el rol `agent` (acotado a `/career/*` y a la subida de archivos). La extracción del harness a `cjhirashi-career-ai` (ADR-029, spec 009) quedó a medias: 63 de 164 tareas.

## Decisión

- El subsistema de agentes con Bedrock **no está operativo** y no forma parte de lo que el proyecto ofrece hoy.
- Los agentes de IA son **externos**: se conectan por la API con un token de rol `agent` y operan sobre los registros del dueño del portafolio.
- La spec 009 se **aplaza** (`estado: deferred`). `cjhirashi-career-ai` no se despliega y Qdrant no tiene consumidor operativo.
- Diseñar de nuevo un arnés de agentes propio queda como **evolución contemplada**, sin compromiso ni fecha; puede que no se integre.

## Qué no cambia

El código del subsistema (rutas `/bedrock`, tablas `bedrock_*`, perfiles, pantallas del Admin) sigue en el repositorio y en la imagen desplegada. Esta decisión cambia lo que se documenta y se ofrece; no retira código. Retirarlo requiere una spec propia.

## Consecuencias

- La documentación del subsistema (`docs/BEDROCK-SYSTEM.md`, `cjhirashi-career-api/docs/BEDROCK-HARNESS.md` y los documentos que lo describen) se conserva como referencia de diseño y lleva un aviso de estado.
- La ficha pública del portafolio describe agentes externos con acceso acotado; no menciona agentes internos, Bedrock ni Qdrant.
- La auditoría con estado anterior y posterior (`audit_logs`) existe solo en las rutas de Bedrock: las escrituras de un agente externo por `/career/*` no la generan.
- Qdrant se **retiró el 2026-11-11** (orden del propietario): sin contenedor, sin `qdrant-client`, sin indexado en las escrituras, sin `search_knowledge_base` ni los endpoints de la base de conocimiento y de la memoria semántica. Las variables de AWS siguen en el despliegue; el resto del subsistema Bedrock sigue en el código.
