"""FastAPI backend entry point — runs on 127.0.0.1 only."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from verbamind.backend.api.router import router
from verbamind.config.config import get_backend_port, get_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="VerbaMind Backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()


def main():
    import uvicorn

    port = get_backend_port()
    uvicorn.run(app, host="127.0.0.1", port=port)
