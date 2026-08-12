"""Manual database test — create, query, verify all 7 models.

Usage: python scripts/test_db.py
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use a temporary database so it doesn't conflict with the real one
tmpdir = tempfile.mkdtemp()
db_path = os.path.join(tmpdir, "test.db")
os.environ["VERBAMIND_TEST_DB"] = db_path

from verbamind.backend.database import models  # noqa: F401, E402
from verbamind.backend.database.base import Base  # noqa: E402
from verbamind.config import config  # noqa: E402

# Override DB URL to use test-specific file
config._config = config._DEFAULT_CONFIG.copy()
config._config["database"]["url"] = f"sqlite+aiosqlite:///{db_path}"

from verbamind.backend.database.connection import get_engine, get_session_factory  # noqa: E402
from verbamind.backend.database.models import (  # noqa: E402
    AuditLog,
    BIRPResult,
    NonverbalResult,
    Patient,
    Psychologist,
    Session,
    Transcript,
)


async def main():
    engine = get_engine()

    print("=== Database Manual Test ===\n")

    # 1. Init tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[1/5] Tables created ✓")

    factory = get_session_factory()

    async with factory() as session:
        # 2. Create patient + psychologist
        patient = Patient(name="Andi Pratama", age=30, gender="male", notes="Pasien baru")
        psych = Psychologist(name="Dr. Sari", license_number="LIC-TEST-001", specialization="Clinical")
        session.add_all([patient, psych])
        await session.flush()
        print(f"[2/5] Created: Patient(id={patient.id}), Psychologist(id={psych.id}) ✓")

        # 3. Create session
        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test_demo.vera",
            status="recorded",
        )
        session.add(ses)
        await session.flush()
        print(f"[3/5] Created: Session(id={ses.id}, status={ses.status}) ✓")

        # 4. Create transcript + NonverbalResult + BIRP
        transcript = Transcript(
            session_id=ses.id,
            speaker="patient",
            text="Saya merasa cemas akhir-akhir ini, dok.",
            start_time=0.0, end_time=3.5,
        )
        nv = NonverbalResult(
            session_id=ses.id,
            frame=10,
            timestamp=0.25,
            current_loudness=-30.5,
            baseline_loudness=-32.0,
            delta_loudness=1.5,
            loudness_category="No Significant Change",
            current_pitch=120.0,
            baseline_pitch=118.0,
            delta_pitch=2.0,
            pitch_category="No Significant Change",
        )
        birp = BIRPResult(
            session_id=ses.id,
            behavior="Pasien menunjukkan gejala kecemasan ringan.",
            intervention="Psikolog melakukan teknik grounding dan CBT.",
            response="Pasien merespons positif, melaporkan penurunan detak jantung.",
            plan="Lanjutkan sesi minggu depan dengan fokus manajemen kecemasan.",
        )
        audit = AuditLog(action="session_created", details=f'{{"session_id": {ses.id}}}')
        session.add_all([transcript, nv, birp, audit])
        await session.commit()
        print(f"[4/5] Created: Transcript, NonverbalResult(frame={nv.frame}), BIRP, AuditLog ✓\n")

    # 5. Query all data
    async with factory() as s2:
        session = s2
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        print("[5/5] Query results:")
        print("-" * 60)

        result = await session.execute(select(Patient).where(Patient.id == patient.id))
        p = result.scalar_one()
        print(f"Patient: {p.name}, age={p.age}, gender={p.gender}")

        result = await session.execute(select(Psychologist).where(Psychologist.id == psych.id))
        ps = result.scalar_one()
        print(f"Psychologist: {ps.name}, license={ps.license_number}")

        result = await session.execute(
            select(Session).where(Session.id == ses.id)
            .options(selectinload(Session.transcripts), selectinload(Session.nonverbal_results))
        )
        s = result.scalar_one()
        print(f"Session: id={s.id}, status={s.status}, created={s.created_at}")
        for t in s.transcripts:
            print(f"  Transcript: [{t.speaker}] \"{t.text}\" ({t.start_time:.1f}s-{t.end_time:.1f}s)")
        for nv in s.nonverbal_results:
            print(f"  Nonverbal: frame={nv.frame} loud={nv.loudness_category} pitch={nv.pitch_category}")

        result = await session.execute(
            select(BIRPResult).where(BIRPResult.session_id == ses.id)
        )
        birp = result.scalar_one()
        print(f"BIRP:")
        print(f"  B (Behavior):     {birp.behavior}")
        print(f"  I (Intervention): {birp.intervention}")
        print(f"  R (Response):     {birp.response}")
        print(f"  P (Plan):         {birp.plan}")

        result = await session.execute(select(AuditLog))
        logs = result.scalars().all()
        print(f"Audit Logs: {len(logs)} entries")
        for log in logs:
            print(f"  [{log.created_at}] {log.action}: {log.details}")

        print("-" * 60)

        # Cascade delete test
        await session.delete(s)
        await session.commit()
        result = await session.execute(select(Transcript).where(Transcript.id == transcript.id))
        assert result.scalar_one_or_none() is None
        result = await session.execute(select(NonverbalResult).where(NonverbalResult.id == nv.id))
        assert result.scalar_one_or_none() is None
        result = await session.execute(select(BIRPResult).where(BIRPResult.id == birp.id))
        assert result.scalar_one_or_none() is None
        print("Cascade delete: Transcript, Nonverbal, BIRP all removed ✓")

    print("\n✅ All database tests passed")

    # Cleanup
    await engine.dispose()
    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"Cleaned up: {tmpdir}")


if __name__ == "__main__":
    asyncio.run(main())
