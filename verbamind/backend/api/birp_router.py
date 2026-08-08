"""BIRP generation API router — Qwen2.5 + RAG clinical note generation.

Endpoints:
- POST /api/v1/birp/generate — Generate BIRP notes from merged verbatim (with RAG)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/birp")


class BIRPRequest(BaseModel):
    """Request schema for BIRP generation."""

    session_id: str = Field(..., description="ID sesi konseling")
    merged_verbatim: list[dict[str, Any]] = Field(
        ...,
        description="List of merged transcript segments with speaker, text, start, end, emotion",
        min_length=1,
    )


class BIRPResponse(BaseModel):
    """Response schema for generated BIRP notes."""

    success: bool
    birp: dict[str, str] | None = None
    error: str | None = None


@router.post("/generate", response_model=BIRPResponse)
async def generate_birp(request: BIRPRequest) -> dict[str, Any]:
    """Generate BIRP clinical notes from merged verbatim transcript.

    Pipeline: verbatim → narrative → RAG retrieval → LLM → BIRP JSON.
    Uses Qwen2.5:7B-Instruct via Ollama with FAISS-based clinical knowledge retrieval.

    Args:
        request: BIRPRequest with session_id and merged_verbatim segments.

    Returns:
        BIRPResponse with behavior, intervention, response, plan keys.
    """
    try:
        generator = BIRPGenerator()
        birp = generator.generate(request.merged_verbatim)
        return {"success": True, "birp": birp, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("BIRP generation failed")
        raise HTTPException(status_code=500, detail=f"BIRP generation failed: {e}")
