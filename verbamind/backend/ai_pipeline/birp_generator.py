"""BIRP Generator — orchestrates RAG retrieval + LLM generation.

Combines:
1. Verbatim parsing (transcript → narrative)
2. RAG retrieval (narrative → clinical context)
3. LLM generation (prompt + context → BIRP JSON)

Adapted from Verbamind_RAG's main_rag.py pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

# Import at module level for mock patching in tests
from verbamind.backend.ai_pipeline.llm import LLMWrapper  # noqa: F401
from verbamind.backend.ai_pipeline.rag.retriever import RAGRetriever  # noqa: F401

from verbamind.backend.ai_pipeline.prompts.birp_prompt import (
    BIRP_REQUIRED_KEYS,
    build_system_prompt,
    validate_birp_output,
)
from verbamind.backend.ai_pipeline.rag.verbatim_parser import (
    merge_transkrip_to_narrative,
)

logger = logging.getLogger(__name__)


class BIRPGenerator:
    """Generates BIRP clinical notes from merged verbatim transcripts.

    Orchestrates: verbatim → narrative → RAG retrieval → LLM → BIRP JSON.
    """

    def __init__(
        self,
        llm_wrapper=None,
        retriever=None,
    ) -> None:
        """Initialize the BIRP generator.

        Args:
            llm_wrapper: LLMWrapper instance (created lazily if None).
            retriever: RAGRetriever instance (created lazily if None).
        """
        self._llm = llm_wrapper
        self._retriever = retriever

    @property
    def llm(self):
        """Lazy-init LLM wrapper."""
        if self._llm is None:
            self._llm = LLMWrapper()
        return self._llm

    @property
    def retriever(self):
        """Lazy-init RAG retriever."""
        if self._retriever is None:
            self._retriever = RAGRetriever()
        return self._retriever

    def _verbatim_to_text(
        self,
        merged_verbatim: list[dict[str, Any]],
    ) -> str:
        """Convert merged verbatim segments to narrative text.

        Args:
            merged_verbatim: List of merged segments with speaker, text, emotion.

        Returns:
            Narrative text string.
        """
        adapted = {
            "id_sesi": "unknown",
            "transkrip": [
                {
                    "speaker": seg.get("speaker", "unknown").capitalize(),
                    "teks": seg.get("text", ""),
                    "emosi": seg.get("emotion", ""),
                }
                for seg in merged_verbatim
            ],
        }
        return merge_transkrip_to_narrative(adapted, include_speaker=True, include_emotion=True)

    def generate(
        self,
        merged_verbatim: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Generate BIRP clinical notes from merged verbatim.

        Full pipeline:
        1. Convert merged verbatim to narrative text
        2. Retrieve relevant clinical context via RAG
        3. Build system prompt with context + transcript
        4. Call LLM for BIRP JSON generation
        5. Validate and fill missing BIRP keys

        Args:
            merged_verbatim: List of enriched transcript segments
                (output of merge_service.MergeService.merge()).

        Returns:
            Dictionary with keys: behavior, intervention, response, plan.

        Raises:
            ValueError: If merged_verbatim is empty.
        """
        if not merged_verbatim:
            raise ValueError("merged_verbatim tidak boleh kosong.")

        # Step 1: Convert to narrative
        narrative = self._verbatim_to_text(merged_verbatim)
        logger.info(f"Generated narrative ({len(narrative)} chars)")

        # Step 2: RAG retrieval
        try:
            context = self.retriever.retrieve(narrative)
            logger.info(f"Retrieved context ({len(context)} chars)")
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}; proceeding without context")
            context = "(Tidak ada konteks referensi tambahan yang ditemukan.)"

        # Step 3: Build prompt
        prompt = build_system_prompt(context=context, transcript=narrative)

        # Step 4: Call LLM
        try:
            result = self.llm.generate_json(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            result = {}

        # Step 5: Validate output
        birp = validate_birp_output(result)
        return birp
