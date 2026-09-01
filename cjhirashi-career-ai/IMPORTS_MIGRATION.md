# Import Migration Guide (FASE 3 Continuation)

## Overview

When copying `services/bedrock/` from the monolith, several imports need to be adjusted because:
1. Bedrock modules reference `models.*` from the monolith DB layer
2. Bedrock modules reference `database` module (SQLAlchemy session)
3. Some modules reference `config` settings from the main API
4. Some reference other `services/*` from the main API

## Strategy

We'll use a **minimal dependency approach**:
- Keep bedrock/* **internal** (no changes to its own logic)
- Create **adapter modules** in IA service to bridge to Orchestrator API
- Bedrock modules read/write through adapters, not direct DB

## Required Changes by Module

### High Priority (Used in agent_loop execution)

| Module | Issue | Fix |
|---|---|---|
| **agent_loop.py** | Imports `from database import get_db_sync` | Remove — use async via orchestrator_client |
| **agent_profiles.py** | Imports `from models import ...` | These stay (internal profiles, don't change) |
| **tools.py** | Imports `from services.linkedin_service` | **BLOCKED** — LinkedInService moved to integrations (FASE 4) |
| **tools.py** | Imports `from models.user` | Inject via parameter from caller (bedrock.py) |
| **usage_logger.py** | Imports `from database import AsyncSessionLocal` | Use orchestrator_client.log_agent_usage() |

### Medium Priority (Called by routers)

| Module | Issue | Fix |
|---|---|---|
| **converse_client.py** | AWS imports | ✅ Already present in IA service config |
| **embeddings.py** | Qdrant imports | ✅ Config.QDRANT_URL already set |
| **history_manager.py** | Imports `from database import AsyncSessionLocal` | Use orchestrator_client for session data |

### Low Priority (Helper modules)

| Module | Issue | Fix |
|---|---|---|
| **prompt.py** | No DB access | ✅ No changes needed |
| **budget.py** | Imports `from database` for state persistence | ⚠️ TODO: Refactor to Redis/Postgres via Orchestrator |

## Import Blockers & Solutions

### 1. LinkedIn Service Not Available in IA Service (FASE 4)

**Location:** `tools.py` line ~200 (LinkedIn publishing tool)

**Problem:**
```python
from services.linkedin_service import create_post  # Doesn't exist in IA service
```

**Solution (Temporary, until FASE 4):**
```python
# Option A: Make tool optional (skip if LinkedIn unavailable)
try:
    from services.linkedin_service import create_post
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False

# Option B: Call via Orchestrator API
# orchestrator_client.publish_to_linkedin(user_id, text, image_url)
```

### 2. Database Session in Agent Loop

**Location:** Multiple modules

**Problem:**
```python
from database import AsyncSessionLocal  # Monolith session factory
async with AsyncSessionLocal() as db:
    result = await db.execute(...)
```

**Solution:**
Replace DB calls with orchestrator_client:
```python
# Before
async with AsyncSessionLocal() as db:
    await db.execute(insert(AgentSystemTask).values(...))

# After
await orchestrator_client.create_task(user_id, auth_token, task_data)
```

### 3. Models Imports

**Location:** `tools.py`, `prompt.py`, etc.

**Problem:**
```python
from models.user import User
from models.work_history import WorkHistory
```

**Solution:**
- Keep imports (these are **read-only schema definitions**, not DB access)
- Inject actual data from Orchestrator API:
```python
# In bedrock.py router
user_data = await orchestrator_client.get_user(user_id, token)
career_data = await orchestrator_client.get_career_data(user_id, token)

# Pass to agent_loop
await run_agent_loop(..., user_data=user_data, career_data=career_data)
```

## Step-by-Step Fix Order

### Phase 3a (Now)
1. ✅ Copy modules (done)
2. ⏳ Update imports in bedrock.py + bedrock_tasks.py routers
3. ⏳ Create wrapper functions for DB access → orchestrator_client

### Phase 3b (Next)
1. Fix tools.py LinkedIn tool (temporary skip or Orchestrator call)
2. Fix usage_logger.py (call orchestrator_client)
3. Fix history_manager.py (if needed)

### Phase 3c (Testing)
1. Run pytest tests/unit/bedrock/
2. Mock orchestrator_client in tests
3. Verify agent loop still works

## Verification Checklist

```bash
# After import fixes:
cd cjhirashi-career-ai

# 1. Syntax check
python3 -m py_compile src/routes/bedrock.py src/routes/bedrock_tasks.py

# 2. Run tests
pytest tests/unit/bedrock/ -v --tb=short

# 3. Docker build
docker build -t cjhirashi-career-ai .

# 4. Smoke test (in docker-compose)
docker compose up ai
curl http://localhost:8010/health
```

## Files to Edit

Priority order:
1. **cjhirashi-career-ai/src/routes/bedrock.py** (main router)
   - Remove `get_db` dependency
   - Use `orchestrator_client` for career data
   - Pass `auth_token` from request headers

2. **cjhirashi-career-ai/src/routes/bedrock_tasks.py** (task runner)
   - Similar changes to bedrock.py

3. **cjhirashi-career-ai/src/services/tools.py** (agent tools)
   - Handle LinkedIn tool gracefully
   - Use orchestrator_client for writes

4. **cjhirashi-career-ai/src/services/usage_logger.py**
   - Call orchestrator_client.log_agent_usage()

## Not Changing

- ✅ All bedrock/* modules that are internal (agent_loop, profiles, prompt, etc.)
- ✅ Model definitions (read-only schema)
- ✅ Test suite (will need minor fixture updates)

---

**Estimated time to complete all import fixes:** 2-3 hours
**Next: Tackle bedrock.py and bedrock_tasks.py imports**
