"""Dashboard API — live stat cards and recent sessions."""

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from verbamind.backend.database.connection import get_session_factory
from verbamind.backend.database.models import Patient, Session

router = APIRouter(prefix="/api/v1/dashboard")


@router.get("/stats")
async def stats() -> dict:
    factory = get_session_factory()
    async with factory() as db:
        # Naive UTC to match SQLite's func.now() (server_default on DateTime).
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_patients = (
            await db.execute(select(func.count()).select_from(Patient))
        ).scalar_one()
        sessions_this_month = (
            await db.execute(
                select(func.count())
                .select_from(Session)
                .where(Session.created_at >= month_start)
            )
        ).scalar_one()
        birp_pending = (
            await db.execute(
                select(func.count())
                .select_from(Session)
                .where((Session.birp_status.is_(None)) | (Session.birp_status != "Selesai"))
            )
        ).scalar_one()
        audio_pending = (
            await db.execute(
                select(func.count())
                .select_from(Session)
                .where(Session.audio_status == "Menunggu keputusan")
            )
        ).scalar_one()

        recent = (
            (await db.execute(select(Session).order_by(Session.id.desc()).limit(10)))
            .scalars()
            .all()
        )
        patient_ids = {s.patient_id for s in recent}
        patients = {}
        if patient_ids:
            patients = {
                p.id: p
                for p in (
                    await db.execute(
                        select(Patient).where(Patient.id.in_(patient_ids))
                    )
                ).scalars().all()
            }
        recent_rows = []
        for s in recent:
            patient = patients.get(s.patient_id)
            recent_rows.append(
                {
                    "id": s.id,
                    "date": s.created_at.strftime("%d %b %Y") if s.created_at else "—",
                    "patient_name": patient.name if patient else "—",
                    "duration_seconds": s.duration_seconds or 0,
                    "birp_status": s.birp_status or "Belum",
                    "audio_status": s.audio_status or "Tersimpan",
                }
            )

        return {
            "status": "ok",
            "stats": {
                "total_patients": total_patients,
                "sessions_this_month": sessions_this_month,
                "birp_pending": birp_pending,
                "audio_pending": audio_pending,
            },
            "recent_sessions": recent_rows,
        }
