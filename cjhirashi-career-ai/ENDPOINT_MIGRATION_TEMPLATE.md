# Endpoint Migration Template - GET /model Example

## Current State (bedrock.py - commented out)

```python
# @router.get("/model", response_model=BedrockModelStatusResponse, ...)
# async def get_model(current_user: User = Depends(get_current_user)):
#     _require_configured()
#     try:
#         current_model_id = await bedrock_service.get_current_model()
#     except BedrockError as e:
#         raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
#     available = [
#         BedrockModelOption(model_id=model_id, **info)
#         for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
#     ]
#     return BedrockModelStatusResponse(current_model_id=current_model_id, available_models=available)
```

## AFTER Migration (NEXT SESSION)

### Step 1: Uncomment endpoint

```python
@router.get("/model", response_model=BedrockModelStatusResponse, 
            summary="Get the active chat model and the switchable allow-list")
async def get_model(request: Request):  # ← CHANGED from current_user: User = Depends(...)
    """Get available models and current selection."""
    _require_configured()
    
    # Extract auth token
    auth_token = get_auth_token(request)  # ← NEW
    user_id = extract_user_id_from_token(auth_token)  # ← NEW
    
    try:
        current_model_id = await bedrock_service.get_current_model()
    except BedrockError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    
    available = [
        BedrockModelOption(model_id=model_id, **info)
        for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
    ]
    return BedrockModelStatusResponse(current_model_id=current_model_id, available_models=available)
```

## Changes Made:

1. ✅ Uncommented function
2. ✅ Changed signature from `current_user: User = Depends(get_current_user)` to `request: Request`
3. ✅ Added `auth_token = get_auth_token(request)` call
4. ✅ Added `user_id = extract_user_id_from_token(auth_token)` call
5. ⏳ Keep bedrock_service calls for now (will migrate to orchestrator_client in FASE 4)

## Notes:

- The `user_id` is extracted but not used in this endpoint (GET /model is not user-specific)
- If model selection were user-specific, we'd use it: `await bedrock_service.get_current_model(user_id)`
- No database access needed for this endpoint
- Follows the same pattern as `/chat` endpoint

---

## PATCH /model Example

Same pattern, but also has a payload:

```python
@router.post("/model", response_model=BedrockModelStatusResponse, 
             summary="Switch the chat model")
async def switch_model(
    payload: BedrockModelSwitchRequest,  # ← Keep this
    request: Request,  # ← CHANGED from current_user: User = Depends(...)
):
    """Switch to a different model."""
    _require_configured()
    auth_token = get_auth_token(request)  # ← NEW
    user_id = extract_user_id_from_token(auth_token)  # ← NEW
    
    if payload.model_id not in settings.BEDROCK_AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown model_id: {payload.model_id}",
        )
    
    try:
        await bedrock_service.switch_model(payload.model_id)  # Could add user_id if needed
    except BedrockError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    
    available = [
        BedrockModelOption(model_id=model_id, **info)
        for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
    ]
    return BedrockModelStatusResponse(current_model_id=payload.model_id, available_models=available)
```

---

## Test for GET /model

After uncommenting, verify with pytest:

```bash
# Collect only (no execution)
pytest --collect-only tests/unit/bedrock/test_bedrock_errors.py

# Run if tests exist for this endpoint
pytest tests/unit/bedrock/ -k "model" -v
```

---

## Next Endpoints (Same Pattern)

All other endpoints follow this exact pattern:

1. Find the commented-out endpoint in bedrock.py or bedrock_tasks.py
2. Change `current_user: User = Depends(get_current_user)` → `request: Request`
3. Remove `db: AsyncSession = Depends(get_db)` (if present)
4. Add token extraction lines at top:
   ```python
   auth_token = get_auth_token(request)
   user_id = extract_user_id_from_token(auth_token)
   ```
5. Replace `current_user.id` with `user_id` throughout
6. If endpoint needs database access, replace with `orchestrator_client` calls

---

## Commit Message Template

```
FASE 3: Migrate GET/PATCH /model endpoints

- Updated endpoint signatures to use Request + token extraction
- Removed current_user: User = Depends(get_current_user) dependencies
- Added get_auth_token() and extract_user_id_from_token() calls
- No database access changes needed for model endpoints
- Verified with pytest --collect-only

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```
