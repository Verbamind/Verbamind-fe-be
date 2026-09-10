"""Settings & model endpoints — list installed Ollama models, get/set LLM config."""

from fastapi import APIRouter
from pydantic import BaseModel

from verbamind.config.llm_settings import (
    get_llm_base_url,
    get_settings,
    list_ollama_models,
    resolve_llm_model,
    save_settings,
)

router = APIRouter(prefix="/api/v1")


class LLMSettingsUpdate(BaseModel):
    llm_model: str
    ollama_base_url: str | None = None


@router.get("/models")
async def get_models():
    return {"models": list_ollama_models()}


@router.get("/settings/llm")
async def get_llm_settings():
    return {
        "llm_model": resolve_llm_model(),
        "ollama_base_url": get_llm_base_url(),
    }


@router.put("/settings/llm")
async def update_llm_settings(payload: LLMSettingsUpdate):
    settings = dict(get_settings())
    settings["llm_model"] = payload.llm_model.strip()
    if payload.ollama_base_url and payload.ollama_base_url.strip():
        settings["ollama_base_url"] = payload.ollama_base_url.strip()
    save_settings(settings)
    return {
        "llm_model": resolve_llm_model(),
        "ollama_base_url": get_llm_base_url(),
    }
