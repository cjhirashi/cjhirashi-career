# Revisiones Alembic (`alembic/versions/`)

Cadena lineal de **53 revisiones**; head actual: `6b2d8f4a1c57` (`project_drop_legacy_text_fields`, 2026-11-07). Comprueba el estado real con `alembic heads` y `alembic history`; esta página resume la cadena por tema (no por archivo, para no desactualizarse).

**Última actualización**: 2026-11-10

## Cómo está organizada la cadena

| Tramo | Contenido |
|---|---|
| **Base (agosto 2026)** | CV y certificaciones, harness Bedrock, plataformas de empleo, prompts por perfil, IDs prefijados, usuarios de sistema, estilos y metodología de PDF, `personal_profile`, renombrado de IDs `agent_*` |
| **Agentes y tareas** | Perfil del agente en conversaciones, metodologías por perfil, secciones del Admin, tareas programadas del agente, subtareas y notificaciones, fotos de perfiles, herramientas por perfil, caché de tokens de Bedrock, reglas globales |
| **Secciones del Admin** | PK sintético `sec-N`, retiro de descripciones y del texto libre de metodologías, metodologías ligadas a secciones (`section_ids`) |
| **Carrera y vacantes** | Plataformas de búsqueda y su clave foránea con CVs, etapa del proceso y estado calculado, textos descriptivos de empresa y puesto, empresa objetivo, `projects.slug` y `notebook_url`, tecnologías a competencias, cambios de identidad y certificaciones |
| **Observabilidad** | Registro de errores (`error_reports`), roles de acceso de usuario (`access_role`) |
| **Analítica del portafolio** | Tablas `portal_*` (sitios, visitantes, visitas, metas, embudos, anotaciones, reglas de canal, agregados diarios), eventos con sesión, latitud/longitud y duración, `portal_about` |
| **Contacto** | `contact_messages` |
| **Proyectos del portafolio** | Documentación en tres campos markdown (`presentacion`, `tecnico`, `estado`) con `estado_verificado_el`, y retiro de los campos de texto anteriores (ADR-030; head) |

## Convenciones

- Los nombres son `<hash>_<descripcion>.py`; el hash lo genera Alembic (`alembic revision -m "descripcion"`).
- Una revisión que migra datos se ensaya antes en una copia con datos reales y lleva un `downgrade` real; respaldo previo de la base antes de aplicarla en producción.
- Fuente de verdad del esquema para despliegues: `alembic upgrade head`. Guía y dominios: [../../docs/DATABASE.md](../../docs/DATABASE.md).
