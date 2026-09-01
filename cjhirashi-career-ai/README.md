# cjhirashi-career-ai — Microservicio de IA

**FASE 3:** Extracción del servicio de Bedrock Agent del monolito.

## Descripción

Microservicio dedicado a la orquestación del agente Bedrock, separando la lógica de IA del CRUD de carrera. El servicio recibe solicitudes SSE desde el Orquestador (API principal), ejecuta el agent loop, y llama de vuelta al Orquestador para operaciones de lectura/escritura de datos de carrera.

## Arquitectura

```
Orquestador (API) ──POST /ai/chat (SSE)──> IA Service
                   <──Events (SSE)──────────
                   
IA Service
├── services/bedrock/ (24 modules)
│   ├── agent_loop.py — Motor de ejecución del agente
│   ├── agent_profiles.py — Perfiles L1/L2/L3
│   ├── tools.py — Tool definitions (escritura de carrera)
│   ├── converse_client.py — Cliente Bedrock
│   ├── embeddings.py — Cliente Qdrant
│   ├── usage_logger.py — Tracking de gasto Bedrock
│   └── ... (18 módulos más)
├── routes/bedrock.py — 32 endpoints (chat, management)
├── routes/bedrock_tasks.py — 3 endpoints (task execution)
└── HTTP client → Orchestrator API (lectura/escritura de carrera)
```

## Estado: ESTRUCTURA BASE

- ✅ Dockerfile
- ✅ requirements.txt
- ✅ src/config.py (Bedrock-focused settings)
- ✅ src/main.py (FastAPI skeleton)
- 🔜 Copiar services/bedrock/ (24 modules)
- 🔜 Implementar routes/bedrock.py
- 🔜 Implementar routes/bedrock_tasks.py
- 🔜 Cliente HTTP hacia Orchestrator
- 🔜 Migrar tests/unit/bedrock

## Siguientes Pasos (FASE 3 Continuación)

### 1. Copiar módulos de Bedrock

```bash
cp -r ../cjhirashi-career-api/src/services/bedrock/ src/services/
```

Modificar imports en cada módulo (cambiar rutas relativas si es necesario).

### 2. Copiar tests

```bash
cp -r ../cjhirashi-career-api/tests/unit/bedrock/ tests/unit/
```

### 3. Implementar routers

Copiar de `cjhirashi-career-api/src/routes/bedrock.py` a `src/routes/bedrock.py`:
- Todos los 32 endpoints de chat, agent management, usage metrics
- Cambiar dependencias de `get_db` (Orchestrator API calls vía HTTP)
- Mantener SSE streaming sin cambios

### 4. Crear HTTP client a Orchestrator

```python
# src/clients/orchestrator_client.py
class OrchestratorClient:
    async def get_career(user_id: str) -> dict
    async def create_work_history(...) -> dict
    async def update_career_stage(...) -> dict
    # ... resto de CRUD operations vía Orchestrator API
```

### 5. Ajustar budget.py

Hoy `budget.py` usa variables en memoria que se resetean al desplegar.
Opciones:
- Guardar en Postgres (tabla `agent_system_usage_logs`)
- Guardar en Redis (con TTL por día)

Recomendación: Postgres para persistencia real, Redis para caché rápido.

### 6. Testear

```bash
cd cjhirashi-career-ai
pytest tests/unit/bedrock/ -v
```

## Configuración (.env)

```bash
# .env
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=...
BEDROCK_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=career_knowledge
ORCHESTRATOR_API_BASE_URL=http://api:8001
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_URL=https://files.cjhirashi.com
```

## Docker Compose Integration

Agregar a `docker-compose.yml`:

```yaml
ai:
  build:
    context: ./cjhirashi-career-ai
    dockerfile: Dockerfile
  container_name: cjhirashi_career_ai
  ports:
    - "8010:8010"
  env_file: .env
  environment:
    ORCHESTRATOR_API_BASE_URL: http://api:8001
    QDRANT_URL: http://qdrant:6333
    BEDROCK_REGION: ${BEDROCK_REGION}
    AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
    AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
  depends_on:
    postgres:
      condition: service_healthy
    qdrant:
      condition: service_started
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Routing (post-FASE 5 Gateway)

Hoy (FASE 3 en desarrollo):
```
Caddy → API:8001/api/bedrock/* → Orquestador
                    (después de mover)
Caddy → API:8001/api/bedrock/* → Gateway:8000
                          (ruta)
        Gateway → IA:8010/ai/* (interno)
```

## Rollback Plan

Strangler fig: Mantener `services/bedrock/` en monolito hasta confirmar IA service estable.

1. Comentar nuevo router en Orchestrator
2. Dejar routers viejos activos en API
3. Cambiar Gateway para enrutar a API en lugar de IA
4. Desmontar IA service

## Notas de Implementación

- **Aislamiento de datos:** No copiar tablas de BD del monolito. El IA service solo escribe a través de HTTP calls al Orchestrator (patrón strangler).
- **Autenticación:** JWT mismo que en API (no diferente scope). Token viene desde Orchestrator vía header.
- **SSE streaming:** Pasar eventos sin cambios (misma forma que hoy consume cjhirashi-career-admin).
- **Agentes del sistema:** Budget, history, delegations — todo persiste en Postgres vía Orchestrator API.

## Estado de Progreso

- Estructura base: ✅ COMPLETA
- Siguiente: Copiar módulos de Bedrock + implementar routers (Est. 4-6 horas)

---

**Ver:** Monolito original en `../cjhirashi-career-api/src/services/bedrock/`
