---
titulo: "Esquema de BD del harness y migración de datos (spec 009)"
tipo: contrato
feature_id: "009"
fecha: 2026-10-13
---

# BD del harness (`career_ai_db`) y migración desde `career_db`

Fuente del inventario: metadatos SQLAlchemy de los modelos `bedrock_*` de la API
(2026-10-13). Cambios respecto al origen: **sólo** se eliminan las FK a `users.id`
(cruzan de BD, D-01/D-02); `user_id` queda `VARCHAR(20)` indexado, sin FK.

## 1. Tablas (11 migradas + 1 nueva: `bedrock_agent_memory`)

| Tabla | PK | FK conservadas | Columnas |
|---|---|---|---|
| `bedrock_agent_delegation` | `profile_id` VARCHAR(50) | — | target_ids JSONB!, updated_at! |
| `bedrock_agent_profile_photos` | `profile_id` | — | photo_url VARCHAR(1024)!, updated_at! |
| `bedrock_agent_profile_prompts` | `profile_id` | — | system_prompt_suffix TEXT!, updated_at! |
| `bedrock_agent_profile_tools` | `profile_id` | — | tool_names JSONB, updated_at! |
| `bedrock_conversations` | `id` VARCHAR(20) (`bco-N`) | — | user_id!, session_id VARCHAR(100)!, session_type VARCHAR(20)!, agent_profile_id VARCHAR(50), title VARCHAR(255)!, created_at!, updated_at! |
| `bedrock_conversation_messages` | `id` (`bcm-N`) | `conversation_id → bedrock_conversations.id` ON DELETE CASCADE | role VARCHAR(20)!, content TEXT!, created_at! |
| `bedrock_custom_tools` | `id` (`bct-N`) | — | name VARCHAR(100)!, url TEXT!, headers JSON, is_enabled!, created_at! |
| `bedrock_settings` | `id` INTEGER (serial) | — | system_prompt, global_rules, active_model_id, orchestrator_model_id, max_round_trips!, history_window!, daily_budget_usd NUMERIC(10,4)!, updated_at! |
| `bedrock_tasks` | `id` (`btk-N`) | `parent_id → bedrock_tasks.id` ON DELETE CASCADE | user_id!, title!, description, status!, notes, assignee_type!, agent_profile_id, scheduled_at, due_at, priority!, sort_order!, is_blocking!, execute_on_turn!, turn_notified_at, execution_result, executed_at, error_message, created_at!, updated_at! |
| `bedrock_usage_logs` | `id` INTEGER (serial) | — | user_id!, session_id VARCHAR(64)!, model_id!, input/output/cache_read/cache_write_tokens!, estimated_cost_usd NUMERIC(12,6)!, created_at! |
| `bedrock_usage_round_logs` | `id` INTEGER (serial) | — | user_id!, session_id VARCHAR(100)!, model_id, round_type!, tool_name, agent_profile_id, tokens (4)!, estimated_cost_usd!, notes, created_at! |

| `bedrock_agent_memory` (**nueva**, RF-022) | `id` VARCHAR(20) (`bam-N`) | — | user_id!, kind VARCHAR(20)! (`note`\|`fact`\|`manual`), agent_profile_id VARCHAR(50) (NULL = global del usuario), text TEXT!, search_vector TSVECTOR (columna generada `to_tsvector('spanish', text)`) con índice GIN, source VARCHAR(20)! (`harness`\|`qdrant_import`), source_ref VARCHAR(100) (id del punto Qdrant, único por `user_id`+`source_ref` para idempotencia), created_at! |

(`!` = NOT NULL.) El detalle fino (longitudes, defaults, índices) lo fija la migración
inicial **generada desde los modelos copiados** y verificada por un test de esquema que la
compara con la lista anterior. No se renombran tablas (D-13: paridad; el rediseño neutro
queda para spec posterior).

### Secuencias de ID (hazard de la Constitución: secuencias desincronizadas)

- `bco_id_seq`, `bcm_id_seq`, `bct_id_seq`, `btk_id_seq`, `bam_id_seq` (memoria) (IDs prefijados) y las secuencias
  `serial` de `bedrock_settings`, `bedrock_usage_logs`, `bedrock_usage_round_logs`.
- La migración inicial las **crea**; el script de copia hace `setval(seq, max(n)+1)` por
  secuencia tras copiar. Test: tras la copia, insertar una fila nueva no colisiona.
- `services/id_generator.py` del harness: copia mínima (los 5 prefijos), mismo
  mecanismo `before_insert` + `nextval`.

## 2. Migraciones propias

`cjhirashi-career-ai/alembic/` (Alembic propio; `alembic_version` en `career_ai_db`).
Revisión inicial `0001_initial_harness_schema`. El harness NUNCA toca el Alembic de la API
(Art. 4 se enmienda en el ADR-029: el Alembic de `career_db` ya no gobierna el harness).
Se verifica contra la BD real antes de aplicar (Art. 4: no asumir `upgrade head` = realidad).

## 3. Copia de datos — `cjhirashi-career-ai/scripts/copy_from_career_db.py`

Script **offline** (no es parte del servicio; el servicio no tiene ninguna variable
`SOURCE_*` y un test AST/regex sobre `src/` prohíbe cualquier referencia a `career_db`,
RF-003).

```
python scripts/copy_from_career_db.py --source $SOURCE_DATABASE_URL --dest $AI_DATABASE_URL \
       [--direction api-to-ai|ai-to-api] [--report ai_copy_report.json] [--dry-run]
```

- **Verificación de esquema previa:** compara `information_schema.columns` de `career_db` con el esquema de `career_ai_db` (tipo, longitud, nulabilidad); si difieren, falla sin copiar (los modelos del harness no llevan `server_default` y la BD dev de la API tiene `ALTER` directos).
- Origen en **transacción `READ ONLY`**. Destino: `INSERT ... ON CONFLICT (pk) DO UPDATE`
  (idempotente, re-ejecutable), en orden de dependencias (conversations → messages;
  tasks por `parent_id`: raíces primero).
- **Conserva identificadores** (RF-007). Tras copiar: `setval` de secuencias.
- **Reporte** (stdout + `ai_copy_report.json`):

```json
{"generated_at": "...", "direction": "api-to-ai", "ok": true,
 "tables": {"bedrock_tasks": {"source": N, "dest": N, "missing_in_dest": 0, "checksum_ok": true}, "...": {}}}
```

- **RF-007:** exit code ≠ 0 y `ok:false` si para alguna tabla `source != dest` justo tras
  copiar (en la primera copia el destino está vacío, así que deben ser iguales) o
  `missing_in_dest > 0`. `checksum_ok` = hash de la lista ordenada de PK + `updated_at`/
  `created_at` por tabla (detecta filas distintas con mismo conteo).
- `--direction ai-to-api` es la ruta **inversa** (rollback de etapa 2 y downgrade de etapa
  3): upsert hacia las tablas `bedrock_*` de `career_db` mientras existan (o tras el
  `downgrade` que las recrea).
- **Verificación para el DROP (RF-011):** modo `--verify-only` genera el mismo reporte con
  `mode:"verify"`; en ese modo la condición es `missing_in_dest == 0` (el destino puede
  tener **más** filas que el origen: la etapa 2 ya escribe en el harness).

## 4. Migración de la API que elimina las 11 tablas (RF-011)

`cjhirashi-career-api/alembic/versions/<nueva>_drop_bedrock_tables.py`
(`down_revision = "d8f2b5a13c97"`, único head hoy; se re-verifica al implementar).

- `upgrade()`:
  1. **Guarda previa:** exige env `AI_COPY_REPORT` apuntando a un reporte con `ok:true`,
     `generated_at` ≤ 24 h, las 11 tablas y `missing_in_dest == 0`; si no existe o no
     cumple → `RuntimeError` **antes de cualquier DDL**. Además compara, tabla a tabla,
     los PK actuales de `career_db` contra el reporte (el origen no cambió desde la
     verificación).
  2. `DROP TABLE` en orden inverso de dependencias, `IF EXISTS`, idempotente (patrón
     `f8a9b1c2d3e4`: `sa.inspect`). Elimina también las secuencias `bco/bcm/bct/btk`.
- `downgrade()`: **recrea la estructura** (tablas, FKs, índices, secuencias) con el DDL de
  las migraciones originales (`a1b2c3d4e5f6`, `f6a7b8c9d0e1`, `a7b8c9d0e1f2`, `b1c2d3e4f5a6`,
  `b8c9d0e1f2a3`, `c2d3e4f5a6b7`, `c9d0e1f2a3b4`, `f7a8b9c0d1e2`...) copiado literal (una
  migración no importa modelos vivos). Los datos NO los recrea el `downgrade`: se restauran
  con `--direction ai-to-api` o del backup (RNF-002).
- Test de migración con dobles (patrón `test_vacancy_process_stage_migration.py`): guarda
  falla sin reporte / con reporte `ok:false` / con reporte viejo, sin emitir DDL; `upgrade`
  elimina; `downgrade` recrea las 11 con las columnas de §1.

## 5. Conteos de referencia (a rellenar en la operación, RNF-002)

El conteo real por tabla en origen/destino NO se conoce en el plan (no se tocó la BD
viva). Se registra en la evidencia de la tarea de etapa 1 (`SELECT count(*)` por tabla,
solo con OK explícito del usuario).

## 6. Memoria del agente: Qdrant → Postgres (RF-022, D-15)

La memoria (notas del agente `_AGENT_NOTE_KEY="agent-notes"`, hechos aprendidos y notas
manuales) vive **sólo en Qdrant** (colección `career_knowledge`, payload con `user_id`,
`agent_profile_id`, `text`). Script offline separado:
`cjhirashi-career-ai/scripts/migrate_memory_from_qdrant.py`:

- Lee Qdrant por *scroll* (solo lectura) filtrando los puntos de memoria (`resource_key`
  de memoria/`agent-notes`; **los puntos de registros de carrera indexados NO se migran**,
  son derivados del CRUD que se elimina). Inserta en `bedrock_agent_memory` con
  `INSERT ... ON CONFLICT (user_id, source_ref) DO NOTHING` (idempotente).
- **Reporte** `memory_migration_report.json`: por `kind` y por `user_id`: `source` (puntos
  leídos), `dest` (filas con `source='qdrant_import'`), `skipped_invalid`; `ok:false` y exit
  ≠ 0 si `source != dest + skipped_invalid`. Los puntos inválidos (sin texto/`user_id`) se
  listan, no se pierden en silencio.
- **Gate previo a retirar Qdrant:** la tarea de etapa 3b que borra servicio y volumen
  exige un reporte `ok:true` reciente + snapshot de Qdrant (RNF-002). El conteo real no se
  conoce al planificar (no se consultó Qdrant).
- Búsqueda: `retrieve_memory_records` pasa de similitud vectorial a
  `search_vector @@ websearch_to_tsquery('spanish', :q)` ordenado por `ts_rank`; sin
  embeddings. Cambia la relevancia (no la forma del contrato `GET /bedrock/memory/records`).
  Idioma `spanish`; configurable (`MEMORY_FTS_CONFIG`).
- `GET /bedrock/memory/events` sigue saliendo de `bedrock_conversation_messages`.

## 7. Qué NO se migra

- Puntos de Qdrant que indexan registros de carrera y la KB (se descartan con Qdrant, D-04).
- `audit_logs` **se queda en la API** (D-19), no se mueve.
