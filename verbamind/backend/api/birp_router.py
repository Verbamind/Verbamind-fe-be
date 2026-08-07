"""BIRP generation API router — placeholder for Qwen2.5 integration (deferred)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/birp")


@router.post("/generate")
async def generate_birp(request: dict):
    return {"status": "not_implemented", "message": "Qwen2.5 BIRP pipeline pending (Step 8 deferred)"}
