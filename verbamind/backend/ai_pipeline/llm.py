"""LLM Wrapper — Ollama integration for any locally installed model.

The model name and base URL are resolved at runtime via
verbamind.config.llm_settings (env var > settings.json > default), so the
user can switch models (3b, 7b, llama, mistral, ...) without a code change.
"""

import logging

from verbamind.config.llm_settings import (
    get_llm_base_url,
    resolve_llm_model,
)

logger = logging.getLogger(__name__)

TEMPERATURE = 0.3

# Backwards-compatible module-level constants (resolved once at import).
MODEL_LLM = resolve_llm_model()
URL_OLLAMA = get_llm_base_url()


class LLMWrapper:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self._base_url = base_url or get_llm_base_url()
        self._model = model or resolve_llm_model()
        self._llm = None

    def _init(self):
        from langchain_ollama import ChatOllama

        self._llm = ChatOllama(
            base_url=self._base_url,
            model=self._model,
            temperature=TEMPERATURE,
            format="json",
        )

    def generate(self, prompt: str, system: str | None = None) -> str:
        if self._llm is None:
            self._init()
        if system is not None:
            from langchain_core.messages import HumanMessage, SystemMessage

            response = self._llm.invoke(
                [SystemMessage(content=system), HumanMessage(content=prompt)]
            )
        else:
            response = self._llm.invoke(prompt)
        return response.content
