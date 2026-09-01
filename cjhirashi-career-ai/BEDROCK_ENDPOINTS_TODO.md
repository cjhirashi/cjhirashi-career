# Bedrock Endpoints Migration TODO - FASE 3 Continuation

**Status:** 1/21 endpoints migrated (5%)  
**Estimated effort:** 2-3 hours  
**Template:** src/routes/bedrock.py `/chat` endpoint

---

## Migration Pattern (Apply to all remaining endpoints)

### BEFORE:
```python
@router.get("/model", response_model=BedrockModelStatusResponse)
async def get_model(current_user: User = Depends(get_current_user)):
    # Uses current_user.id, bedrock_service calls
```

### AFTER:
```python
@router.get("/model", response_model=BedrockModelStatusResponse)
async def get_model(request: Request):
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)
    # Uses user_id, bedrock_service/orchestrator_client calls
```

---

## Endpoints to Migrate (20+)

### Priority 1: Model Management (2 endpoints)
- [ ] `GET /model` — Get active model + available options
- [ ] `PATCH /model` — Switch model

**Changes:**
- Remove `current_user: User = Depends(get_current_user)`
- Add `request: Request`
- Extract user_id from token
- Keep bedrock_service calls (for now)

### Priority 2: Conversation Management (4 endpoints)
- [ ] `GET /conversations` — List conversations
- [ ] `GET /conversations/{session_id}` — Get messages
- [ ] `PATCH /conversations/{session_id}` — Rename
- [ ] `DELETE /conversations/{session_id}` — Delete

**Changes:**
- Remove both `current_user` and `db: AsyncSession = Depends(get_db)`
- Add `request: Request`
- Extract user_id from token
- **Database access:** Replace `await db.execute(select(...))` with `await orchestrator_client.get_conversations(user_id)`

### Priority 3: Usage Metrics (2 endpoints)
- [ ] `GET /usage-metrics` — Get token usage + costs
- [ ] `GET /budget` — Get daily budget status

**Changes:**
- Replace all `AgentSystemUsageLog` queries with `orchestrator_client.get_usage_metrics(user_id)`
- Keep budget logic (bedrock_service calls)

### Priority 4: Memory Management (8 endpoints)
- [ ] `GET /memory` — List memory records
- [ ] `POST /memory` — Create memory entry
- [ ] `GET /memory/{id}` — Get memory entry
- [ ] `PATCH /memory/{id}` — Update entry
- [ ] `DELETE /memory/{id}` — Delete entry
- [ ] `GET /memory/events/{session_id}` — Memory events
- [ ] `POST /memory/manual` — Manual memory input
- [ ] `GET /memory/types` — List memory types

**Changes:**
- Remove db dependency (all memory is via orchestrator_client)
- Extract user_id from token
- Call `orchestrator_client.get_memory()`, `set_memory()`, etc.

### Priority 5: Custom Tools (4 endpoints)
- [ ] `GET /tools` — List custom tools
- [ ] `POST /tools` — Create tool
- [ ] `PATCH /tools/{tool_id}` — Enable/disable
- [ ] `DELETE /tools/{tool_id}` — Delete tool

**Changes:**
- Remove `current_user` and `db` dependencies
- Extract user_id
- Replace bedrock_service calls with orchestrator_client

### Priority 6: Profile Management (3+ endpoints)
- [ ] `GET /profile` — Get agent profile
- [ ] `PATCH /profile` — Update profile settings
- [ ] `GET /profiles` — List profiles
- [ ] Other profile-related endpoints

**Changes:**
- Extract user_id
- Call orchestrator_client for all operations

### Priority 7: Task Management (1 endpoint)
- [ ] `POST /agent-tasks/{item_id}/run` — Execute task

**Changes:**
- Located in `bedrock_tasks.py`
- Extract user_id from token
- Call `orchestrator_client.execute_task(user_id, task_id)`

### Priority 8: Audit Log (2 endpoints)
- [ ] `GET /audit-log` — List audit entries
- [ ] `POST /audit-log/{id}/restore` — Restore entry

**Changes:**
- Extract user_id
- Call orchestrator_client for audit operations

### Priority 9: Agent Settings (2+ endpoints)
- [ ] `GET /instructions` — Get system prompt
- [ ] `PATCH /instructions` — Update system prompt
- [ ] `GET /rules` — Get global rules
- [ ] `PATCH /rules` — Update global rules
- [ ] `GET /catalog` — Get agent catalog

**Changes:**
- Extract user_id
- Keep bedrock_service calls (local logic) OR call orchestrator_client for persistence

---

## Database Access Patterns to Replace

### Pattern 1: Direct SQLAlchemy queries
```python
# BEFORE:
result = await db.execute(select(AgentSystemUsageLog).where(...))
logs = result.scalars().all()

# AFTER:
logs = await orchestrator_client.get_usage_logs(user_id, filters)
```

### Pattern 2: Model creation/update
```python
# BEFORE:
obj = Model(**data)
db.add(obj)
await db.commit()

# AFTER:
obj = await orchestrator_client.create_resource(user_id, resource_type, data)
```

### Pattern 3: Conditional imports
```python
# Handle LinkedIn service (FASE 4 blocker):
try:
    from services.linkedin_service import create_post
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False
```

---

## Blockers & Workarounds

### 1. LinkedIn Service (FASE 4 Dependency)
- **Blocker:** `tools.py` references `services.linkedin_service`
- **Temp solution:** Conditional import + return error if unavailable
- **Permanent:** FASE 4 integration

### 2. Storage Service (FASE 4 Dependency)
- **Blocker:** `tools.py` imports `storage_service`
- **Temp solution:** Already commented out
- **Permanent:** FASE 4 integration

### 3. JWT Token Verification
- **Current:** Returns placeholder `"usr-2"`
- **TODO:** Call `orchestrator_client.verify_token()` OR implement JWT locally
- **Impact:** All endpoints

---

## Testing Strategy

After migrating each endpoint:

```bash
# 1. Syntax check
python3 -m py_compile src/routes/bedrock.py

# 2. Import check
pytest --collect-only tests/unit/bedrock/test_bedrock_errors.py

# 3. Run specific test
pytest tests/unit/bedrock/test_bedrock_errors.py -v

# 4. Full suite (at end)
pytest tests/unit/bedrock/ -v --tb=short
```

---

## Commit Strategy

### Commit 1: Model endpoints
```
FASE 3: Migrate GET/PATCH /model endpoints

- Updated endpoint signatures to use Request + token extraction
- Removed current_user and db dependencies
- Tested endpoint definitions with --collect-only
```

### Commit 2: Conversation endpoints
```
FASE 3: Migrate conversation CRUD endpoints

- GET /conversations, /conversations/{id}
- PATCH /conversations/{id}, DELETE /conversations/{id}
- Replace db queries with orchestrator_client calls
```

### Commit 3-5: Remaining endpoints (batch)
```
FASE 3: Migrate memory, tools, audit endpoints

- Memory management (8 endpoints)
- Custom tools CRUD (4 endpoints)
- Audit log endpoints (2 endpoints)
```

### Commit 6: Testing
```
FASE 3: Fix test imports and verify

- Update test fixtures for new endpoint signatures
- Run pytest tests/unit/bedrock/
- Docker build test
```

---

## Time Estimate

| Task | Time |
|---|---|
| Model endpoints (GET, PATCH) | 30 min |
| Conversation endpoints (4) | 45 min |
| Usage/Budget endpoints (2) | 20 min |
| Memory endpoints (8) | 60 min |
| Custom tools (4) | 30 min |
| Audit + Agent settings (5) | 45 min |
| Test fixture updates + pytest | 45 min |
| **TOTAL** | **4 hours** |

---

## Next Session Checklist

- [ ] Start with GET /model as template (30 min)
- [ ] Apply pattern to Priority 1-2 endpoints (45 min)
- [ ] Migrate database queries to orchestrator_client (45 min)
- [ ] Fix remaining import errors (30 min)
- [ ] Run pytest suite (20 min)
- [ ] Docker build test (15 min)
- [ ] Smoke test /chat endpoint with SSE (10 min)

**Total: ~3-4 hours**

---

## Reference Files

- `src/routes/bedrock.py` — Migrated /chat endpoint (example)
- `IMPORT_FIXES_DETAILED.md` — Detailed fix guide (lines 75-85)
- `src/services/bedrock_service_wrapper.py` — Compatibility layer
- `src/clients/orchestrator_client.py` — HTTP bridge to monolith
