"""Process API — full AI pipeline endpoint.

POST /api/v1/process
Input: {
    "session_db_id": int,          # DB session id
    "audio_path": str,             # .vera (encrypted) or .wav/.mp3 (plain)
    "key_hex": str | null,         # ephemeral AES key (hex) for .vera — dev only
    "language": "id"
}

Pipeline: decrypt → split channels → Whisper STT (both) →
SpeechToNonverbalInformation (patient only) → merge → RAG + LLM → BIRP.
Persists Transcript, NonverbalResult, BIRPResult; updates Session status.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from verbamind.backend.api.audit_helper import log_action
from verbamind.backend.api.path_guard import resolve_audio_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/process")


class ProcessRequest(BaseModel):
    session_db_id: int
    audio_path: str
    key_hex: str | None = None
    language: str = "id"
    channels: int = 1


def _build_process_service(language: str):
    from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator
    from verbamind.backend.ai_pipeline.llm import LLMWrapper
    from verbamind.backend.ai_pipeline.merge_service import MergeService
    from verbamind.backend.ai_pipeline.process_service import ProcessService
    from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever
    from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler
    from verbamind.backend.ai_pipeline.speech_to_nonverbal_service import (
        SpeechToNonverbalService,
    )
    from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

    retriever = RAGRetriever(index_dir="faiss_index")
    llm = LLMWrapper()
    return ProcessService(
        transcribe_service=TranscribeService(mock=False, language=language),
        nonverbal_service=SpeechToNonverbalService(),
        merge_service=MergeService(),
        speaker_labeler=SpeakerLabeler(),
        birp_generator=BIRPGenerator(retriever=retriever, llm=llm),
    )


def _load_audio(audio_path: str, key_hex: str | None) -> bytes:
    """Load audio file; decrypt .vera when a key is provided."""
    from verbamind.security.encryptor import decrypt_bytes

    path = resolve_audio_path(audio_path)
    if not path.exists():
        raise FileNotFoundError("Audio tidak ditemukan")

    raw = path.read_bytes()
    if path.suffix.lower() == ".vera":
        if not key_hex:
            raise ValueError("File .vera butuh kunci untuk dekripsi")
        return decrypt_bytes(raw, bytes.fromhex(key_hex))
    return raw  # plain .wav/.mp3 — pipeline handles format detection


async def _persist_result(session_db_id: int, result: dict) -> None:
    from sqlalchemy import select

    from verbamind.backend.database.connection import get_session_factory
    from verbamind.backend.database.models import (
        NonverbalResult,
        Session,
        Transcript,
    )

    factory = get_session_factory()
    async with factory() as db:
        session = (
            await db.execute(select(Session).where(Session.id == session_db_id))
        ).scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session DB id {session_db_id} tidak ditemukan")

        # Replace previous transcripts / nonverbal rows for this session
        old_ts = (
            await db.execute(select(Transcript).where(Transcript.session_id == session_db_id))
        ).scalars().all()
        for t in old_ts:
            await db.delete(t)
        old_nv = (
            await db.execute(
                select(NonverbalResult).where(NonverbalResult.session_id == session_db_id)
            )
        ).scalars().all()
        for nv in old_nv:
            await db.delete(nv)

        for seg in result.get("transcript", []):
            db.add(Transcript(
                session_id=session_db_id,
                speaker=seg.get("speaker", "unknown"),
                text=seg.get("text", "")[:5000],
                start_time=float(seg.get("start", 0.0)),
                end_time=float(seg.get("end", 0.0)),
            ))

        for frame in result.get("nonverbal", []):
            db.add(NonverbalResult(
                session_id=session_db_id,
                frame=int(frame.get("frame", 0)),
                timestamp=float(frame.get("timestamp", 0.0)),
                current_loudness=float(frame.get("current_loudness", 0.0)),
                baseline_loudness=float(frame.get("baseline_loudness", 0.0)),
                delta_loudness=float(frame.get("delta_loudness", 0.0)),
                loudness_category=str(frame.get("loudness_category", "")),
                current_pitch=frame.get("current_pitch"),
                baseline_pitch=frame.get("baseline_pitch"),
                delta_pitch=frame.get("delta_pitch"),
                pitch_category=str(frame.get("pitch_category", "")),
            ))

        birp = result.get("birp")
        if birp:
            from verbamind.backend.api.birp_service import upsert_birp_result

            await upsert_birp_result(db, session_db_id, birp, birp_status="Draft")

        await db.commit()


@router.post("")
async def process_session(payload: ProcessRequest) -> dict:
    try:
        audio_data = _load_audio(payload.audio_path, payload.key_hex)
    except Exception:
        logger.exception("Gagal memuat audio")
        return {"status": "error", "message": "Gagal memuat audio"}

    import anyio

    service = _build_process_service(payload.language)
    try:
        result = await anyio.to_thread.run_sync(
            lambda: service.process(
                audio_data,
                session_id=f"DB-{payload.session_db_id}",
                channels=payload.channels,
            )
        )
    except Exception:
        logger.exception("Pipeline gagal")
        return {"status": "error", "message": "Terjadi kesalahan internal"}

    try:
        await _persist_result(payload.session_db_id, result)
    except Exception:
        logger.exception("Persist gagal")
        result["errors"] = result.get("errors", []) + ["Persist failed"]

    await log_action(
        "Proses AI",
        f"Pipeline AI sesi={payload.session_db_id} status={result.get('status')}",
    )

    return {
        "status": result.get("status"),
        "errors": result.get("errors", []),
        "birp": result.get("birp"),
        "merged": result.get("merged", []),
        "transcript_count": len(result.get("transcript", [])),
        "nonverbal_count": len(result.get("nonverbal", [])),
    }
