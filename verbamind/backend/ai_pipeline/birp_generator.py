"""BIRP Generator — orchestrates RAG + LLM pipeline.

Adapted from Verbamind_RAG src/main_rag.py — full pipeline: verbatim → RAG → LLM → BIRP JSON.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from verbamind.backend.ai_pipeline.llm import MODEL_LLM, LLMWrapper
from verbamind.backend.ai_pipeline.prompts.birp_prompt import (
    BIRP_REQUIRED_KEYS,
    SYSTEM_PROMPT,
    build_user_prompt,
    validate_birp_output,
)
from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever
from verbamind.backend.ai_pipeline.rag.verbatim_parser import (
    gabungkan_transkrip_menjadi_narasi,
)

logger = logging.getLogger(__name__)


class BIRPGenerator:
    def __init__(
        self,
        retriever: RAGRetriever,
        llm: LLMWrapper,
        output_dir: str = "output_hasil",
    ):
        self._retriever = retriever
        self._llm = llm
        self._output_dir = Path(output_dir)

    def generate(
        self,
        verbatim_data: dict[str, Any],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Jalankan pipeline lengkap: verbatim → narasi → RAG → LLM → BIRP."""
        sid = session_id or verbatim_data.get("id_sesi", "SESI-TIDAK-DIKETAHUI")

        # Tahap 1: Gabungkan transkrip menjadi narasi
        narasi = gabungkan_transkrip_menjadi_narasi(
            verbatim_data,
            sertakan_nama_speaker=True,
            sertakan_label_emosi=True,
        )
        logger.info(f"Narasi transkrip: {len(narasi)} karakter")

        # Tahap 2: Retrieval dari FAISS
        try:
            konteks = self._retriever.retrieve(narasi)
        except FileNotFoundError:
            logger.warning("Index FAISS tidak ditemukan, melanjutkan tanpa RAG")
            konteks = "(Tidak ada konteks referensi tambahan yang ditemukan.)"

        # Tahap 3: Panggil LLM (system = instruksi, user = konteks + transkrip)
        user_prompt = build_user_prompt(konteks_referensi=konteks, narasi_transkrip=narasi)
        logger.info("Mengirim prompt ke LLM...")
        response_raw = self._llm.generate(user_prompt, system=SYSTEM_PROMPT)
        birp = self._parse_response(response_raw)
        birp = validate_birp_output(birp)

        # Tahap 4: Simpan hasil
        self._save(sid, birp)

        return birp

    def _parse_response(self, raw: str) -> dict:
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Gagal parsing JSON: {raw[:200]}...")
            return {k: "" for k in BIRP_REQUIRED_KEYS}

    def _save(self, session_id: str, birp: dict) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"BIRP_{session_id}_{ts}.json"
        path = self._output_dir / name
        output = {
            "id_sesi": session_id,
            "waktu_analisis": datetime.now().isoformat(),
            "model_llm": MODEL_LLM,
            "catatan_klinis_birp": birp,
        }
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"BIRP disimpan di: {path}")
        return path
