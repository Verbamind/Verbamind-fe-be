"""FastAPI backend entry point — runs on 127.0.0.1 only."""

import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from verbamind.backend.api.audit_router import router as audit_router
from verbamind.backend.api.birp_router import router as birp_router
from verbamind.backend.api.dashboard_router import router as dashboard_router
from verbamind.backend.api.patients_router import router as patients_router
from verbamind.backend.api.process_router import router as process_router
from verbamind.backend.api.router import router
from verbamind.backend.api.sessions_router import router as sessions_router
from verbamind.backend.api.settings_router import router as settings_router
from verbamind.backend.api.speech_to_nonverbal_router import (
    router as speech_to_nonverbal_router,
)
from verbamind.backend.api.transcribe_router import router as transcribe_router
from verbamind.config.config import get_backend_port
from verbamind.security.token import get_or_create_token

logger = logging.getLogger(__name__)

AUTH_HEADER = "X-VerbaMind-Token"


def require_auth(request: Request) -> None:
    """Reject requests that do not carry the machine-local shared token."""
    expected = get_or_create_token()
    provided = request.headers.get(AUTH_HEADER, "")
    if not secrets.compare_digest(expected, provided):
        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import verbamind.backend.database.models  # noqa: F401 — register all models
    from verbamind.backend.database.base import init_db
    from verbamind.backend.database.connection import get_engine

    get_or_create_token()

    try:
        await init_db(None)
        # Lightweight migration: add columns introduced after initial create_all.
        from sqlalchemy import text

        async with get_engine().begin() as conn:
            existing = (
                await conn.execute(text("PRAGMA table_info(patients)"))
            ).fetchall()
            cols = {row[1] for row in existing}
            if existing and "birth_date" not in cols:
                await conn.execute(
                    text("ALTER TABLE patients ADD COLUMN birth_date VARCHAR(20)")
                )
            if existing and "medical_record" not in cols:
                await conn.execute(
                    text("ALTER TABLE patients ADD COLUMN medical_record VARCHAR(100)")
                )

            sess_cols = (
                await conn.execute(text("PRAGMA table_info(sessions)"))
            ).fetchall()
            sess_names = {row[1] for row in sess_cols}
            for col, ddl in [
                ("duration_seconds", "INTEGER"),
                ("birp_status", "VARCHAR(50)"),
                ("audio_status", "VARCHAR(50)"),
                ("consent_file", "VARCHAR(500)"),
            ]:
                if sess_cols and col not in sess_names:
                    await conn.execute(
                        text(f"ALTER TABLE sessions ADD COLUMN {col} {ddl}")
                    )
    except Exception:
        logger.exception("DB init failed")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="VerbaMind Backend",
        version="0.1.0",
        lifespan=lifespan,
        dependencies=[Depends(require_auth)],
    )

    # No cross-origin access — the API is for the local GUI only.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_methods=[],
        allow_headers=[],
    )

    app.include_router(router)
    app.include_router(birp_router)
    app.include_router(patients_router)
    app.include_router(sessions_router)
    app.include_router(dashboard_router)
    app.include_router(audit_router)
    app.include_router(process_router)
    app.include_router(settings_router)
    app.include_router(speech_to_nonverbal_router)
    app.include_router(transcribe_router)
    return app


app = create_app()


def main():
    import uvicorn

    port = get_backend_port()
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
