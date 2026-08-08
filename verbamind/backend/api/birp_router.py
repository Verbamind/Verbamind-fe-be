"""BIRP API — generate clinical notes via RAG + Qwen2.5."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/birp")


@router.post("/generate")
async def generate_birp(request: dict):
    """Generate BIRP from verbatim transcript.

    Input: {
        "session_id": str,
        "verbatim_segments": [{"speaker": str, "text": str, "start": float, "end": float, "emotion": str|null}]
    }
    """
    try:
        segments = request.get("verbatim_segments", [])
        session_id = request.get("session_id", "SESI-TIDAK-DIKETAHUI")

        transkrip = []
        for s in segments:
            transkrip.append({
                "speaker": s.get("speaker", "Tidak diketahui"),
                "teks": s.get("text", ""),
                "emosi": s.get("emotion", ""),
            })

        verbatim_data = {"id_sesi": session_id, "transkrip": transkrip}

        try:
            from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator
            from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever
            from verbamind.backend.ai_pipeline.llm import LLMWrapper

            retriever = RAGRetriever(index_dir="faiss_index")
            llm = LLMWrapper()
            generator = BIRPGenerator(retriever=retriever, llm=llm)
            birp = generator.generate(verbatim_data=verbatim_data, session_id=session_id)
            return {"status": "ok", "data": birp}
        except FileNotFoundError as e:
            return {
                "status": "partial",
                "message": f"FAISS index not found. Run ingest_knowledge first. {e}",
                "data": None,
            }
        except ImportError as e:
            return {
                "status": "unavailable",
                "message": f"RAG dependencies not installed: {e}",
                "data": None,
            }
    except Exception as e:
        return {"status": "error", "message": str(e), "data": None}
