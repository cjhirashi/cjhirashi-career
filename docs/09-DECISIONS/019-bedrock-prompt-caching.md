# ADR-019: Prompt caching de Bedrock + proyección de campos y truncado por campo

## Estado

Aceptado — 2026-08-27

## Contexto

Trabajando con un agente L2 sobre un registro grande (`projects/prj-43`, ~14 500 caracteres
serializados a JSON), el agente repetía "el contenido está truncado" y no lograba operar el
registro. El análisis reveló dos problemas de eficiencia de tokens:

1. **Truncado ciego de resultados de tools.** `get_career_record` devuelve la fila completa
   (todas las columnas). Si el JSON supera `BEDROCK_MAX_TOOL_RESULT_CHARS` (8 000),
   `truncate_tool_result` **descartaba el registro entero** y lo sustituía por
   `{truncated, preview, message}` con solo los primeros ~7 920 caracteres. El agente perdía
   la mitad de los campos, no sabía cuáles, y releía el registro una y otra vez.

2. **Sin prompt caching.** El bucle de Bedrock (`agent_loop`) reenvía en **cada ronda** (hasta
   `max_round_trips = 6`) el system prompt + las especificaciones de todas las tools + el
   historial (`history_window = 20`) + todos los `toolResult` del turno, y todo se factura a
   precio íntegro de tokens de entrada. `converse_client.converse()` armaba la petición sin
   ningún `cachePoint`. Modelo activo: Claude Haiku 4.5 ($1.00/M entrada); Sonnet 4.5
   disponible ($3.00/M) — ambos soportan prompt caching en Bedrock.

Se descartó **Redis**: no reduce tokens. Bedrock cobra por lo que se envía al modelo, sin
importar de dónde salió el dato en la infraestructura; Redis solo ahorraría consultas a
PostgreSQL y latencia. El patrón que podría respaldar (handle store para lecturas grandes) se
cubre con la BD y estructuras en proceso, sin sumar un servicio nuevo.

## Decisión

### 1. Prompt caching de Bedrock (`cachePoint`) — palanca principal

`converse_client._build_converse_kwargs()` (extraído de `converse()` para poder testearlo)
inserta hasta **3 `cachePoint`** cuando el modelo lo soporta:

- al final de `system` (system prompt, grande y estable dentro de la sesión);
- al final de `toolConfig.tools` (especificaciones de tools, grandes y estables);
- al final del `content` del **último mensaje** (prefijo estable ronda a ronda). Se hace sobre
  una copia superficial del último mensaje para no mutar la lista `messages`, que `agent_loop`
  sigue extendiendo entre rondas.

**Gate por modelo**: `BEDROCK_AVAILABLE_MODELS[<id>]["supports_prompt_cache"] = True` en las dos
entradas Claude 4.5. `_supports_prompt_cache(model_id)` exige además el kill-switch global
`settings.BEDROCK_PROMPT_CACHE_ENABLED` (default `True`). Modelos no-Anthropic (Nova, Llama,
Mistral, DeepSeek) no reciben ningún `cachePoint` — sin riesgo de `ValidationException`.

**Umbral mínimo (crítico)**: Bedrock solo crea la caché si el prefijo **acumulado
`tools`+`system`+`messages` hasta ese `cachePoint`** alcanza el mínimo del modelo:
**4 096 tokens para Claude Haiku 4.5**, **1 024 para Claude Sonnet 4.5** (verificado en la doc de
Bedrock y empíricamente: prefijo de ~2 540 tok → no cachea; ~6 586 tok → cachea). Un `cachePoint`
por debajo del mínimo se ignora en silencio (la request tiene éxito). Consecuencia práctica con
Haiku 4.5: los `cachePoint` de `system` y `tools` casi nunca llegan a 4 096 por sí solos, así que
**solo el `cachePoint` del último mensaje trabaja**, y únicamente cuando el prefijo total del
turno supera 4 096 (turnos con registros grandes o varias rondas con `toolResult` en historial).

**Contabilidad de costos**: Bedrock reporta `cacheReadInputTokens` y `cacheWriteInputTokens`
aparte de `inputTokens` (que ya viene sin los tokens leídos de caché). `parse_converse_response`
y `consume_converse_stream` los capturan; `agent_loop` los acumula en `total_usage`;
`usage_logger._estimate_cost()` los factura con los ratios estándar **0.10×** (lectura) y
**1.25×** (escritura) del precio de entrada del modelo. `budget.py` no cambia: sigue sumando
`estimated_cost_usd`, que ya incluye el costo de caché — el presupuesto diario sigue correcto.

**Migración** `b1c2d3e4f5a6`: columnas `cache_read_tokens` / `cache_write_tokens` (INTEGER,
default 0) en `bedrock_usage_logs` y `bedrock_usage_round_logs`, para desglose en el panel de
costos.

### 2. Proyección de campos en `get_career_record`

Parámetro opcional `fields: string[]` en el schema de la tool. Cuando se pasa, el handler
(`bedrock_service.py`) filtra el registro serializado a `set(fields) | {"id"}`. El system prompt
instruye: en registros grandes (p.ej. `projects`), pedir solo las columnas que se van a leer o
editar en vez de traer el registro completo.

### 3. Truncado por cuota de campos (reemplaza el corte ciego)

`tool_results._cap_record_fields()`: si el resultado tiene forma `{"item": {...}}` y se pasa del
tope, reparte el presupuesto de caracteres disponible (tope − andamiaje JSON − campos cortos −
reserva de marcadores) entre los campos largos y recorta cada uno a esa **cuota dinámica**,
conservando **todas** las claves:

- Cuando el modelo pidió un campo aislado con `fields=[...]`, ese campo recibe casi todo el
  presupuesto (~7,5 KB con tope 8 KB) y un marcador **terminal** ("Es todo lo que cabe en un
  resultado de tool para este campo") que NO invita a repetir la llamada — evita el bucle
  truncado↔dedupe.
- Con varios campos largos, cada uno lleva `…[+N caracteres — pídelo aislado: get_career_record
  fields=['<campo>']]`.
- Valores no-string grandes (JSONB `dict`/`list`) también se recortan, con prefijo
  `[JSON recortado] `.
- Un lazo acotado reduce la cuota si el JSON serializado (con escapes) aún no cabe; en última
  instancia cae al recorte ciego `{truncated, preview, message}`. Listas y otras tools pasan sin
  cambios.

### 4. Dedupe de lecturas idénticas dentro del turno

`agent_loop` mantiene un set `seen_reads` con clave `<tool>:<input canónico>` para las tools de
solo lectura (`get_career_record`, `list_career_record`, `count_career_records`,
`describe_resource_schema`, `search_knowledge_base`). Una llamada idéntica repetida en el mismo
turno no se reejecuta: se responde con una nota corta en vez de reincrustar el payload. Nunca
aplica a escrituras.

**Invalidación tras write**: un write con éxito (directo — `tools.is_write_tool()` — o vía
`delegate_to_specialist` con `affected_resources`) hace `seen_reads.clear()`. Así una relectura
posterior en el mismo turno (p.ej. `get_career_record` → `update_career_record` →
`get_career_record` para confirmar) ve el estado nuevo, no el snapshot previo. El set es
turn-scoped (fresco por turno, nunca persiste entre turnos).

## Eficacia real del prompt caching (por perfil / modelo)

El mecanismo #1 **solo aporta** donde el modelo soporta caché **y** el prefijo del turno supera
el mínimo:

| Perfil(es) | Modelo | ¿Cachea? |
|---|---|---|
| L1 `agent_orchestrator` | Haiku 4.5 | Solo si el turno supera 4 096 tok (turnos base ~2 540 → **no**) |
| L2 `search` / `networking` / `support` / `methodologies` / `settings` / `changelog` | Haiku 4.5 | Solo turnos grandes (≥ 4 096 tok) |
| L2 `digital_presence` / `pdf_design`, L3 `cv_writing` / `cover_letter_writing` | Sonnet 4.5 | Sí, con facilidad (mínimo 1 024) |
| **L2 `agent_professional_identity`** (dueño de `projects`, `identity`, `achievements`, `star-stories`, `work-history`, `personal-profile`) | **Mistral Large** | **No** — sin `supports_prompt_cache` |
| 7× L3 (nova-lite) | Nova Lite | No |

**El caso que originó este ADR (`prj-43`, dueño `agent_professional_identity`) NO se beneficia
del caching hoy** porque ese L2 corre en Mistral Large. Los mecanismos #2–#4 (proyección,
truncado por cuota, dedupe) sí aplican a todos los perfiles y son los que resuelven el bucle de
"contenido truncado". Mover `agent_professional_identity` a Haiku 4.5 (más barato que Mistral
Large, $1/$5 vs $2/$6 por M, y con caché) es un cambio pendiente a evaluar con `ingenieria-llm`
por el impacto en calidad de redacción — **ver ADR-012**.

## Consecuencias

### Positivas

- **Turnos grandes multironda con modelo Claude** (registro grande en contexto, ≥ 2 rondas):
  las rondas ≥ 2 leen el prefijo a 0.10× → ~50–70 % menos costo de entrada en esas rondas.
  Medido: prefijo de 6 586 tok cachea completo y la relectura baja `inputTokens` a 5.
- **Turnos cortos (~2 500 tok) o modelos no-Claude**: sin ahorro (los `cachePoint` sub-mínimo se
  ignoran sin coste). **No es −50/75 % general** como se estimó al inicio.
- El agente ve la **forma completa** de un registro grande aunque no quepa entero, y sabe qué
  campo pedir aislado → se acaba el bucle de "contenido truncado" (mecanismos #2–#4, todos los
  perfiles).
- `fields` permite operar `prj-43` trayendo ~2 KB en vez de ~14,5 KB.
- Panel de costos (`/usage-metrics`) con desglose caché vs. entrada normal y "ahorro por caché".

### Costos / riesgos

- La **escritura** de caché cuesta 1.25× (TTL 5 min). El ahorro es neto solo cuando el prefijo
  se reutiliza dentro del TTL. Si algún día se usa `{"ttl": "1h"}`, la escritura pasa a 2.0× y
  hay que parametrizar `_CACHE_WRITE_RATIO` (hoy fijo a 1.25, con comentario en `usage_logger`).
- La proyección de campos y el truncado por cuota dependen de que el modelo **use** `fields`; el
  system prompt lo induce pero no lo garantiza. Si el modelo pide un `field` inexistente, hoy
  recibe `{"item": {"id": ...}}` sin pista — mejora pendiente: devolver hint de columnas válidas.
- **Pre-existente, detectado en la revisión**: `budget.get_daily_spend_usd` suma
  `bedrock_usage_logs` + `bedrock_usage_round_logs`, que se escriben ambas por turno → posible
  doble conteo del gasto diario. Ajeno a este ADR; las columnas de caché heredan el mismo patrón.
  El endpoint `/usage-metrics` (nuevo desglose de caché) lee **solo** `bedrock_usage_logs`, sin
  doble conteo.
- Kill-switch: `BEDROCK_PROMPT_CACHE_ENABLED=false` desactiva (1) por completo si Bedrock diera
  problemas con `cachePoint`.

### Alternativas rechazadas

- **Redis / cache de infraestructura**: no reduce tokens (ver Contexto).
- **Subir `BEDROCK_MAX_TOOL_RESULT_CHARS`**: haría caber `prj-43` pero **aumenta** los tokens
  reenviados en cada ronda — lo contrario del objetivo.
- **Bajar `history_window` / `max_round_trips`**: con caching el historial reenviado cuesta
  ~10 %, así que acortarlo aporta poco; `max_round_trips` es presupuesto de finalización de
  tarea, no una perilla de costo. Ambos siguen siendo editables en caliente desde el Admin
  (tabla `bedrock_settings`) si hiciera falta afinarlos con datos reales.

## Validación

Revisado por dos especialistas globales (2026-08-27):

- **aws-bedrock** — veredicto *funcional con reservas*. Confirmó contra doc oficial: colocación
  de los 3 `cachePoint`, copia segura de `messages`, nombres de campos de `usage`, ratios
  0.10×/1.25× (TTL 5 min), parseo streaming. Reserva principal: umbral de 4 096 tok en Haiku 4.5
  hace que la "palanca principal" solo rinda en turnos grandes. Fuentes: doc de prompt caching
  de Amazon Bedrock, model card de Claude Haiku 4.5, doc de Anthropic.
- **harness-agentes** — veredicto *funcional con reservas*. Detectó y se corrigieron: (B1)
  `seen_reads` servía datos previos a un write del mismo turno → ahora se limpia tras write;
  (B2) campo único > tope entraba en bucle truncado↔dedupe → ahora cuota dinámica + marcador
  terminal; (B3) valores JSONB grandes no se recortaban → ahora sí; (B5) rama `except
  BedrockError` no registraba `record_turn_usage` → ahora sí. Pendientes documentados: modelo de
  `agent_professional_identity` (ver arriba) y doble conteo de `budget.py` (pre-existente).

## Referencias

- `cjhirashi-career-api/src/services/bedrock/converse_client.py` — `_build_converse_kwargs`,
  `_supports_prompt_cache`, `_cache_point`, parseo de tokens de caché.
- `cjhirashi-career-api/src/services/bedrock/usage_logger.py` — `_estimate_cost`, `_cache_tokens`,
  `cache_read_savings_usd`.
- `cjhirashi-career-api/src/services/bedrock/tool_results.py` — `_cap_record_fields` (cuota
  dinámica).
- `cjhirashi-career-api/src/services/bedrock/agent_loop.py` — acumulación de caché, `seen_reads`
  + invalidación tras write, `record_turn_usage` en rama de error.
- `cjhirashi-career-api/src/services/bedrock_service.py` — `get_career_record` con `fields`.
- `cjhirashi-career-api/src/routes/bedrock.py` + `src/schemas/bedrock.py` — `/usage-metrics` con
  `cache_read_tokens` / `cache_write_tokens` / `total_cache_savings_usd`.
- `cjhirashi-career-admin/src/components/bedrock/BedrockCostPanel.tsx` — columna "Tokens caché" y
  tarjeta "Ahorro por caché".
- Migración `cjhirashi-career-api/alembic/versions/b1c2d3e4f5a6_bedrock_cache_tokens.py`.
- Tests: `tests/unit/bedrock/test_converse_cache_points.py`, `test_usage_cost_cache.py`,
  `test_tool_results_truncation.py`, `test_dedup_read_tools.py`.
- Relacionado: [ADR-008](./008-bedrock-harness-local.md), [ADR-012](./012-bedrock-three-level-agents.md).
