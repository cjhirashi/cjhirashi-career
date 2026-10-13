"""GET /health - público, sin dependencias externas (R7: no falla si la API está caída)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "cjhirashi-career-ai"}
