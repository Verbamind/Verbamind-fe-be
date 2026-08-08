"""LLM Wrapper — Ollama integration for Qwen2.5:7B-Instruct.

Adapted from Verbamind_RAG src/main_rag.py: inisialisasi_llm_ollama.
"""

import logging

logger = logging.getLogger(__name__)

URL_OLLAMA = "http://localhost:11434"
MODEL_LLM = "qwen2.5:7b-instruct"
TEMPERATURE = 0.3


class LLMWrapper:
    def __init__(self, base_url: str = URL_OLLAMA, model: str = MODEL_LLM):
        self._base_url = base_url
        self._model = model
        self._llm = None

    def _init(self):
        from langchain_ollama import ChatOllama

        self._llm = ChatOllama(
            base_url=self._base_url,
            model=self._model,
            temperature=TEMPERATURE,
            format="json",
        )

    def generate(self, prompt: str) -> str:
        if self._llm is None:
            self._init()
        response = self._llm.invoke(prompt)
        return response.content
