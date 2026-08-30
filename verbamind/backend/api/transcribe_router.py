"""STT API router — transcription endpoint (Whisper)."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from verbamind.backend.api.path_guard import resolve_audio_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stt")


class TranscribeRequest(BaseModel):
    audio_path: str
    language: str = "id"


@router.post("/transcribe")
async def transcribe(payload: TranscribeRequest):
    """Transcribe an audio file inside recordings/ (dev convenience).

    For the full pipeline use POST /api/v1/process instead.
    """
    try:
        path = resolve_audio_path(payload.audio_path)
        if not path.exists():
            return {"status": "error", "message": "Audio tidak ditemukan"}
    except ValueError:
        return {"status": "error", "message": "audio_path tidak valid"}

    import anyio

    from verbamind.backend.ai_pipeline.audio_io import to_mono_wav_bytes
    from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

    svc = TranscribeService(mock=False, language=payload.language)

    def _run():
        wav = to_mono_wav_bytes(path.read_bytes())
        return svc.transcribe(wav)

    try:
        segments = await anyio.to_thread.run_sync(_run)
    except Exception:
        logger.exception("Transkripsi gagal")
        return {"status": "error", "message": "Terjadi kesalahan internal"}

    return {"status": "ok", "count": len(segments), "segments": segments}
