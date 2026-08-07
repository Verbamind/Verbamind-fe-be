"""STT API router — transcription endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/stt")


@router.post("/transcribe")
async def transcribe(request: dict):
    """Transcribe audio from an encrypted .vera file.

    Status: 501 Not Implemented — Whisper model not yet integrated.
    """
    return {"status": "not_implemented", "message": "STT pipeline pending model integration"}
