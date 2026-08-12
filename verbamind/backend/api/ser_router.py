"""SER API — analyze audio for nonverbal cues (loudness + pitch changes)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ser")


@router.post("/analyze")
async def analyze_audio(request: dict):
    """Analyze audio file for nonverbal cues.

    Input: { "audio_path": "recordings/test.vera", "session_id": 1 }
    Output: { "status": "ok", "frame_count": N, "sample": [...] }
    """
    audio_path = request.get("audio_path")
    if not audio_path:
        return {"status": "error", "message": "audio_path required"}

    try:
        from verbamind.backend.ai_pipeline.ser_service import SERService

        svc = SERService()
        results = svc.analyze_file(audio_path)
        return {
            "status": "ok",
            "frame_count": len(results),
            "sample": results[:5] if results else [],
        }
    except FileNotFoundError:
        return {"status": "error", "message": f"Audio file not found: {audio_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
