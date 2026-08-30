"""Shared BIRP persistence helper — single upsert path for BIRPResult rows."""

from sqlalchemy import select

from verbamind.backend.database.models import BIRPResult, Session


async def upsert_birp_result(
    db,
    session_id: int,
    birp: dict,
    birp_status: str = "Draft",
) -> int | None:
    """Upsert a BIRPResult for a session; returns its id (None if session missing)."""
    session = (
        await db.execute(select(Session).where(Session.id == session_id))
    ).scalar_one_or_none()
    if session is None:
        return None

    existing = (
        await db.execute(select(BIRPResult).where(BIRPResult.session_id == session.id))
    ).scalar_one_or_none()
    if existing is None:
        existing = BIRPResult(session_id=session.id)
        db.add(existing)

    existing.behavior = birp.get("behavior", "")
    existing.intervention = birp.get("intervention", "")
    existing.response = birp.get("response", "")
    existing.plan = birp.get("plan", "")
    session.birp_status = birp_status
    return existing.id
