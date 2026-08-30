"""Patients API — CRUD pasien backed by SQLite."""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from verbamind.backend.api.audit_helper import log_action
from verbamind.backend.database.connection import get_session_factory
from verbamind.backend.database.models import Patient, Session

router = APIRouter(prefix="/api/v1/patients")


class PatientIn(BaseModel):
    name: str
    age: int | None = None
    gender: str | None = None
    birth_date: str | None = None
    medical_record: str | None = None
    notes: str | None = None


@router.get("")
async def list_patients() -> dict:
    factory = get_session_factory()
    async with factory() as db:
        rows = (
            (await db.execute(select(Patient).order_by(Patient.id.desc()))).scalars().all()
        )
        counts = dict(
            (
                await db.execute(
                    select(Session.patient_id, func.count())
                    .group_by(Session.patient_id)
                )
            ).all()
        )
        patients = [
            {
                "id": p.id,
                "name": p.name,
                "age": p.age,
                "gender": p.gender,
                "birth_date": p.birth_date or "—",
                "medical_record": p.medical_record or "—",
                "notes": p.notes or "",
                "session_count": counts.get(p.id, 0),
            }
            for p in rows
        ]
        return {"status": "ok", "count": len(patients), "patients": patients}


@router.post("")
async def create_patient(payload: PatientIn) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        patient = Patient(
            name=payload.name,
            age=payload.age,
            gender=payload.gender,
            birth_date=payload.birth_date,
            medical_record=payload.medical_record,
            notes=payload.notes,
        )
        db.add(patient)
        await db.commit()
        await log_action("Buat Pasien", f"Pasien baru ditambahkan: {patient.name}")
        return {"status": "ok", "id": patient.id, "name": patient.name}


@router.get("/{patient_id}")
async def get_patient_detail(patient_id: int) -> dict:
    from sqlalchemy import func

    from verbamind.backend.database.models import Session

    factory = get_session_factory()
    async with factory() as db:
        p = (
            await db.execute(select(Patient).where(Patient.id == patient_id))
        ).scalar_one_or_none()
        if p is None:
            return {"status": "error", "message": "Patient not found"}
        total = (
            await db.execute(
                select(func.count()).select_from(Session).where(Session.patient_id == p.id)
            )
        ).scalar_one()
        return {
            "status": "ok",
            "patient": {
                "id": p.id,
                "name": p.name,
                "age": p.age,
                "gender": p.gender,
                "birth_date": p.birth_date or "—",
                "medical_record": p.medical_record or "—",
                "notes": p.notes or "",
                "session_count": total,
            },
        }


@router.delete("/{patient_id}")
async def delete_patient(patient_id: int) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        p = (
            await db.execute(select(Patient).where(Patient.id == patient_id))
        ).scalar_one_or_none()
        if p is None:
            return {"status": "error", "message": "Patient not found"}
        name = p.name
        await db.delete(p)
        await db.commit()
        await log_action("Hapus", f"Pasien dihapus: {name} (id={patient_id})")
        return {"status": "ok"}
