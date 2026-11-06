# Tests unitarios del harness Bedrock (`tests/unit/bedrock/`)

Cubren `services/bedrock/` y las rutas `/bedrock/*` sin invocar AWS. Documentación del paquete: [src/services/bedrock/README.md](../../../src/services/bedrock/README.md). El CI corre este directorio.

**Última actualización**: 2026-11-05. Agrupados por patrón de nombre; para el detalle, `ls tests/unit/bedrock/`.

| Patrón | Cubre |
|---|---|
| `test_profile_*`, `test_section_profile_resolution`, `test_global_rules`, `test_visual_delegation_prompts` | Perfiles de agente (L1/L2/L3), delegación, herramientas, prompts y reglas globales |
| `test_converse_cache_points`, `test_max_tokens_truncation`, `test_tool_results_truncation`, `test_list_extra_fields`, `test_dedup_read_tools`, `test_required_fields_validation`, `test_progress_nudge` | Bucle Converse: caché de prompts, truncado, proyección de campos y validación de herramientas |
| `test_history_manager` | Historial de conversación |
| `test_usage_cost_cache`, `test_budget_no_double_count` | Costos, presupuesto diario y conteo de uso |
| `test_image_client`, `test_image_pipeline_aspect_ratio`, `test_generate_image_tool` | Generación de imágenes (Stability) |
| `test_knowledge_base_*`, `test_methodology_snippets`, `test_qdrant_orphan_purge` | Base de conocimiento en Qdrant: reindexado, purga de huérfanos y extractos de metodologías (se retiran con el ADR-029) |
| `test_section_routes`, `test_tools_catalog_routes`, `test_admin_section_settings_views` | Rutas de secciones, catálogo de herramientas y vistas de configuración |
