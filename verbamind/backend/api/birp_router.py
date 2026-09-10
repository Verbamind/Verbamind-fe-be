"""BIRP API — generate clinical notes via RAG + Qwen2.5."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/birp")


async def _save_birp_to_db(session_id: str, birp: dict) -> int | None:
    """Resolve session id and persist BIRP result (non-fatal)."""
    from sqlalchemy import select

    from verbamind.backend.api.birp_service import upsert_birp_result
    from verbamind.backend.database.connection import get_session_factory
    from verbamind.backend.database.models import Session

    factory = get_session_factory()
    async with factory() as db:
        db_session = None
        if session_id.startswith("DB-") and session_id[3:].isdigit():
            db_session = (
                await db.execute(
                    select(Session).where(Session.id == int(session_id[3:]))
                )
            ).scalar_one_or_none()
        if db_session is None:
            result = await db.execute(
                select(Session).where(Session.audio_file_path == session_id)
            )
            db_session = result.scalar_one_or_none()
        if db_session is None:
            return None

        db_id = await upsert_birp_result(db, db_session.id, birp, birp_status="Draft")
        await db.commit()
        return db_id


class Segment(BaseModel):
    speaker: str = "Tidak diketahui"
    text: str = ""
    start: float = 0.0
    end: float = 0.0
    emotion: str | None = None


class GenerateBIRPRequest(BaseModel):
    session_id: str = "SESI-TIDAK-DIKETAHUI"
    verbatim_segments: list[Segment] = []


@router.post("/generate")
async def generate_birp(payload: GenerateBIRPRequest) -> dict:
    """Generate BIRP from verbatim transcript."""
    transkrip = [
        {"speaker": s.speaker, "teks": s.text, "emosi": s.emotion or ""}
        for s in payload.verbatim_segments
    ]
    verbatim_data = {"id_sesi": payload.session_id, "transkrip": transkrip}

    try:
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator
        from verbamind.backend.ai_pipeline.llm import LLMWrapper
        from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever

        retriever = RAGRetriever()
        llm = LLMWrapper()
        generator = BIRPGenerator(retriever=retriever, llm=llm)
        birp = generator.generate(
            verbatim_data=verbatim_data, session_id=payload.session_id
        )
        db_id = None
        try:
            db_id = await _save_birp_to_db(payload.session_id, birp)
        except Exception:
            logger.exception("DB save failed")
        return {"status": "ok", "data": birp, "db_id": db_id}
    except FileNotFoundError:
        logger.warning("FAISS index tidak ditemukan")
        return {
            "status": "partial",
            "message": "FAISS index tidak ditemukan. Jalankan ingest_knowledge terlebih dahulu.",
            "data": None,
        }
    except ImportError:
        logger.warning("Dependensi RAG belum terpasang")
        return {
            "status": "unavailable",
            "message": "Dependensi RAG belum terpasang.",
            "data": None,
        }
    except Exception:
        logger.exception("BIRP generation gagal")
        return {"status": "error", "message": "Terjadi kesalahan internal", "data": None}


@router.get("/history")
async def birp_history() -> dict:
    """List saved BIRP results from the database (newest first)."""
    from sqlalchemy import select

    from verbamind.backend.database.connection import get_session_factory
    from verbamind.backend.database.models import BIRPResult

    factory = get_session_factory()
    async with factory() as db:
        rows = (
            (await db.execute(select(BIRPResult).order_by(BIRPResult.id.desc())))
            .scalars()
            .all()
        )
        return {
            "status": "ok",
            "count": len(rows),
            "results": [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "behavior": r.behavior[:100],
                    "intervention": r.intervention[:100],
                    "response": r.response[:100],
                    "plan": r.plan[:100],
                    "created_at": str(r.created_at),
                }
                for r in rows
            ],
        }
