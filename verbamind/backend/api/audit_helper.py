"""Audit helper — writes significant actions to audit_logs table."""

from verbamind.backend.database.connection import get_session_factory
from verbamind.backend.database.models import AuditLog


async def log_action(action: str, details: str = "") -> None:
    """Append an audit entry. Non-fatal: failures are swallowed."""
    try:
        factory = get_session_factory()
        async with factory() as db:
            db.add(AuditLog(action=action, details=details))
            await db.commit()
    except Exception:
        pass
