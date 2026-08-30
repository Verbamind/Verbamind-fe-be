"""SpeechToNonverbalInformation API — analyze audio for nonverbal cues (loudness + pitch changes)."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from verbamind.backend.api.path_guard import resolve_audio_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nonverbal")


class NonverbalRequest(BaseModel):
    audio_path: str


@router.post("/analyze")
async def analyze_audio(payload: NonverbalRequest):
    """Analyze audio file for nonverbal cues.

    Input: { "audio_path": "recordings/test.wav" }
    Output: { "status": "ok", "frame_count": N, "sample": [...] }
    """
    try:
        path = resolve_audio_path(payload.audio_path)
        if not path.exists():
            return {"status": "error", "message": "Audio tidak ditemukan"}
    except ValueError:
        return {"status": "error", "message": "audio_path tidak valid"}

    try:
        from verbamind.backend.ai_pipeline.speech_to_nonverbal_service import (
            SpeechToNonverbalService,
        )

        svc = SpeechToNonverbalService()
        results = svc.analyze_file(str(path))
        return {
            "status": "ok",
            "frame_count": len(results),
            "sample": results[:5] if results else [],
        }
    except FileNotFoundError:
        return {"status": "error", "message": "Audio tidak ditemukan"}
    except Exception:
        logger.exception("Analisis nonverbal gagal")
        return {"status": "error", "message": "Terjadi kesalahan internal"}
