"""Audit API — list audit log entries with optional action/date filters."""

from datetime import datetime, time

from fastapi import APIRouter
from sqlalchemy import select

from verbamind.backend.database.connection import get_session_factory
from verbamind.backend.database.models import AuditLog

router = APIRouter(prefix="/api/v1/audit")


@router.get("")
async def list_audit(
    action: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(500)
        rows = (await db.execute(stmt)).scalars().all()

        dt_from = None
        dt_to = None
        if date_from:
            try:
                dt_from = datetime.combine(
                    datetime.strptime(date_from, "%Y-%m-%d").date(), time.min
                )
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.combine(
                    datetime.strptime(date_to, "%Y-%m-%d").date(), time.max
                )
            except ValueError:
                pass

        out = []
        for r in rows:
            if action and action != "Semua Aksi" and r.action != action:
                continue
            created = r.created_at
            if dt_from and created and created < dt_from:
                continue
            if dt_to and created and created > dt_to:
                continue
            out.append(
                {
                    "timestamp": created.strftime("%Y-%m-%d %H:%M:%S") if created else "—",
                    "action": r.action,
                    "details": r.details or "—",
                }
            )
        return {"status": "ok", "count": len(out), "entries": out}
