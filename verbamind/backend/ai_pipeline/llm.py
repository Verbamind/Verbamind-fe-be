"""Qwen2.5:7B LLM wrapper — interfaces with Ollama for local inference.

Provides two generation modes:
- generate(): Free-text generation
- generate_json(): JSON-forced generation for structured BIRP output

All inference runs locally via Ollama (http://localhost:11434).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

# Import at module level for mock patching in tests
try:
    from langchain_ollama import ChatOllama  # noqa: F401
except ImportError:
    ChatOllama = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class LLMWrapper:
    """Thin wrapper around Ollama for Qwen2.5:7B-Instruct generation.

    Attributes:
        base_url: Ollama API endpoint.
        model: Model identifier in Ollama.
        temperature: Sampling temperature (0.0-2.0), lower = more deterministic.
    """

    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b-instruct"
    temperature: float = 0.3

    def generate(self, prompt: str) -> str:
        """Generate free-text response from the LLM.

        Args:
            prompt: The full prompt (system + user) to send.

        Returns:
            Generated text response.
        """
        if ChatOllama is None:
            logger.warning("langchain_ollama not available; returning mock response")
            return '{"behavior":"mock","intervention":"mock","response":"mock","plan":"mock"}'

        llm = ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
        )
        response = llm.invoke(prompt)
        return response.content

    def generate_json(self, prompt: str) -> dict:
        """Generate JSON-formatted response from the LLM.

        Uses Ollama's JSON mode to enforce valid JSON output.

        Args:
            prompt: The full prompt to send.

        Returns:
            Parsed JSON dictionary.

        Raises:
            json.JSONDecodeError: If the LLM output is not valid JSON.
        """
        if ChatOllama is None:
            logger.warning("langchain_ollama not available; returning mock JSON")
            return {
                "behavior": "[MOCK] Behavior description",
                "intervention": "[MOCK] Intervention description",
                "response": "[MOCK] Response description",
                "plan": "[MOCK] Plan description",
            }

        llm = ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            format="json",
        )
        response = llm.invoke(prompt)
        raw = response.content

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM output as JSON: {raw[:500]}")
            raise
