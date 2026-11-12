# Tests unitarios (`tests/unit/`)

Prueban módulos aislados (servicios, middleware, modelos, esquemas, migraciones) sin red ni servicios externos (MinIO y GitHub se simulan). Por defecto usan SQLite en memoria; las que necesitan secuencias de IDs prefijados requieren `TEST_DATABASE_URL` ([../../docs/TESTING.md](../../docs/TESTING.md)).

**Última actualización**: 2026-11-05. Los archivos se agrupan por **patrón de nombre**; no hay lista por archivo (se desactualiza): usa `ls tests/unit/` o `pytest --collect-only -q`.

| Patrón | Cubre |
|---|---|
| `test_auth*`, `test_middleware*`, `test_config`, `test_database` | Autenticación y JWT, rol `agent`, configuración y base de datos |
| `test_admin_section_migration` | Migración histórica de las secciones del Admin (retiradas) |
| `test_resource_registry`, `test_career_distinct`, `test_work_history_schema`, `test_search_*`, `test_file_upload_migration` | Registro de recursos de carrera, esquemas y migraciones de datos |
| `test_vacancy_*` | Vacantes: etapa del proceso y estado calculado, descripciones de empresa y puesto, URL duplicada, claves foráneas |
| `test_methodology_*`, `test_section_methodologies`, `test_section_tools_derivation` | Metodologías operativas (alcance, indexado, migraciones) y herramientas derivadas de las secciones |
| `test_portal_*` | Analítica del portafolio: modelos, ingesta, sesionización, bots, canales, geografía, dispositivo, metas, motor de métricas, rutas, migración y concurrencia del recálculo diario |
| `test_contact_messages` | Mensajes del formulario de contacto |
| `test_error_report*` | Registro de errores (huella, deduplicación, límite de tasa) |
| `test_github_service` | Cliente de GitHub |
| `test_pdf_generation` | Generación de PDF con WeasyPrint |
| `test_system_readiness` | Comprobación de preparación |

`endpoints-parametrized.test.py` **no se ejecuta**: su nombre no coincide con `python_files = test_*.py` y sus aserciones son triviales (rutas `/api/v1/...` que ya no existen). Pendiente: eliminarlo o reemplazarlo por una prueba de humo real contra los prefijos actuales.
