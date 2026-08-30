"""Sessions API — session detail, history, BIRP update, audio deletion."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from verbamind.backend.api.audit_helper import log_action
from verbamind.backend.database.connection import get_session_factory
from verbamind.backend.database.models import BIRPResult, Patient, Session

router = APIRouter(prefix="/api/v1/sessions")


def _birp_status(session: Session) -> str:
    return session.birp_status or "Belum"


def _fmt_date(value) -> str:
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")
    return str(value)


async def _session_rows(db, patient_id: int | None = None) -> list[dict]:
    stmt = select(Session).order_by(Session.id.desc())
    if patient_id is not None:
        stmt = stmt.where(Session.patient_id == patient_id)
    rows = (await db.execute(stmt)).scalars().all()

    patient_ids = {s.patient_id for s in rows}
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

    out = []
    for s in rows:
        patient = patients.get(s.patient_id)
        out.append(
            {
                "id": s.id,
                "patient_id": s.patient_id,
                "patient_name": patient.name if patient else "—",
                "date": _fmt_date(s.created_at),
                "duration_seconds": s.duration_seconds or 0,
                "birp_status": _birp_status(s),
                "audio_status": s.audio_status or "Tersimpan",
                "audio_file_path": s.audio_file_path or "",
                "consent_file": s.consent_file or "",
            }
        )
    return out


@router.get("")
async def list_sessions(patient_id: int | None = None) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        rows = await _session_rows(db, patient_id)
        return {"status": "ok", "count": len(rows), "sessions": rows}


class SessionCreate(BaseModel):
    patient_id: int
    psychologist_id: int = 1
    duration_seconds: int | None = None
    audio_file_path: str | None = None
    consent_file: str | None = None


@router.post("")
async def create_session(payload: SessionCreate) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        session = Session(
            patient_id=payload.patient_id,
            psychologist_id=payload.psychologist_id,
            duration_seconds=payload.duration_seconds,
            audio_file_path=payload.audio_file_path,
            consent_file=payload.consent_file,
            status="recorded",
            birp_status="Belum",
            audio_status="Tersimpan",
        )
        db.add(session)
        await db.commit()
        await log_action(
            "Buat Sesi",
            f"Sesi verbatim baru dibuat (id={session.id}, pasien={payload.patient_id})",
        )
        return {"status": "ok", "id": session.id}


@router.get("/{session_id}")
async def get_session_detail(session_id: int) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        s = (
            await db.execute(select(Session).where(Session.id == session_id))
        ).scalar_one_or_none()
        if s is None:
            return {"status": "error", "message": "Session not found"}
        patient = (
            await db.execute(select(Patient).where(Patient.id == s.patient_id))
        ).scalar_one_or_none()
        birp = (
            await db.execute(select(BIRPResult).where(BIRPResult.session_id == s.id))
        ).scalar_one_or_none()

        from verbamind.backend.database.models import NonverbalResult, Transcript

        transcript_rows = (
            (
                await db.execute(
                    select(Transcript)
                    .where(Transcript.session_id == s.id)
                    .order_by(Transcript.start_time)
                )
            )
            .scalars()
            .all()
        )
        nonverbal_rows = (
            await db.execute(
                select(NonverbalResult).where(NonverbalResult.session_id == s.id)
            )
        ).scalars().all()

        # Attach nonverbal cue (loudness category) to patient segments by time overlap
        segments = []
        for t in transcript_rows:
            emotion = None
            conf = None
            if t.speaker == "patient":
                best = None
                for nv in nonverbal_rows:
                    if nv.timestamp < t.end_time and (nv.timestamp + 0.025) > t.start_time:
                        if best is None or abs(nv.timestamp - t.start_time) < abs(best.timestamp - t.start_time):
                            best = nv
                if best is not None:
                    emotion = best.loudness_category
                    conf = 0.8
            segments.append({
                "speaker": t.speaker,
                "text": t.text,
                "start": t.start_time,
                "end": t.end_time,
                "emotion": emotion,
                "emotion_confidence": conf,
            })

        return {
            "status": "ok",
            "session": {
                "id": s.id,
                "patient_id": s.patient_id,
                "patient_name": patient.name if patient else "—",
                "date": _fmt_date(s.created_at),
                "duration_seconds": s.duration_seconds or 0,
                "birp_status": _birp_status(s),
                "audio_status": s.audio_status or "Tersimpan",
                "audio_file_path": s.audio_file_path or "",
            },
            "birp": {
                "behavior": birp.behavior,
                "intervention": birp.intervention,
                "response": birp.response,
                "plan": birp.plan,
            }
            if birp
            else None,
            "segments": segments,
            "nonverbal_count": len(nonverbal_rows),
        }


class BIRPIn(BaseModel):
    behavior: str
    intervention: str
    response: str
    plan: str


@router.put("/{session_id}/birp")
async def update_birp(session_id: int, payload: BIRPIn) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        s = (
            await db.execute(select(Session).where(Session.id == session_id))
        ).scalar_one_or_none()
        if s is None:
            return {"status": "error", "message": "Session not found"}

        birp = (
            await db.execute(select(BIRPResult).where(BIRPResult.session_id == s.id))
        ).scalar_one_or_none()
        if birp is None:
            birp = BIRPResult(session_id=s.id)
            db.add(birp)
        birp.behavior = payload.behavior
        birp.intervention = payload.intervention
        birp.response = payload.response
        birp.plan = payload.plan
        s.birp_status = "Selesai"
        await db.commit()
        await log_action("Ubah", f"Ringkasan BIRP disimpan/diedit (sesi={session_id})")
        return {"status": "ok", "session_id": session_id}


@router.delete("/{session_id}/audio")
async def delete_audio(session_id: int) -> dict:
    """Mark audio as deleted (auto-delete policy after review)."""
    from verbamind.backend.api.path_guard import safe_delete_recording

    factory = get_session_factory()
    async with factory() as db:
        s = (
            await db.execute(select(Session).where(Session.id == session_id))
        ).scalar_one_or_none()
        if s is None:
            return {"status": "error", "message": "Session not found"}
        path = s.audio_file_path
        s.audio_status = "Dihapus otomatis"
        await db.commit()
        await log_action("Hapus", f"Audio sesi dihapus (sesi={session_id}, file={path})")
    safe_delete_recording(path)
    return {"status": "ok"}


@router.post("/{session_id}/keep-audio")
async def keep_audio(session_id: int) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        s = (
            await db.execute(select(Session).where(Session.id == session_id))
        ).scalar_one_or_none()
        if s is None:
            return {"status": "error", "message": "Session not found"}
        s.audio_status = "Tersimpan"
        await db.commit()
        await log_action("Ubah", f"Audio sesi dipertahankan (sesi={session_id})")
    return {"status": "ok"}
