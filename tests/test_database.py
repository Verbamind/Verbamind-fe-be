"""TDD tests for database models — RED phase.

Tests relationship integrity, cascade deletes, and schema validation
for all 7 models: Patient, Psychologist, Session, Transcript,
SERResult, BIRPResult, AuditLog.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from verbamind.backend.database import models  # noqa: F401 — triggers model registration
from verbamind.backend.database.base import Base, init_db
from verbamind.backend.database.connection import get_engine


@pytest.fixture
async def engine():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine):
    from verbamind.backend.database.connection import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        yield session


class TestPatientModel:
    async def test_create_patient(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient

        patient = Patient(name="John Doe", age=30, gender="male", notes="Test patient")
        session.add(patient)
        await session.commit()
        await session.refresh(patient)

        assert patient.id is not None
        assert patient.name == "John Doe"
        assert patient.age == 30
        assert patient.gender == "male"

    async def test_patient_str_representation(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient

        patient = Patient(name="Jane", age=25, gender="female")
        assert "Jane" in str(patient)


class TestPsychologistModel:
    async def test_create_psychologist(self, session: AsyncSession):
        from verbamind.backend.database.models.psychologist import Psychologist

        psych = Psychologist(
            name="Dr. Smith", license_number="LIC-001", specialization="Clinical"
        )
        session.add(psych)
        await session.commit()
        await session.refresh(psych)

        assert psych.id is not None
        assert psych.license_number == "LIC-001"

    async def test_psychologist_unique_license(self, session: AsyncSession):
        from verbamind.backend.database.models.psychologist import Psychologist

        p1 = Psychologist(name="A", license_number="DUP-001")
        p2 = Psychologist(name="B", license_number="DUP-001")
        session.add(p1)
        await session.commit()
        session.add(p2)
        with pytest.raises(Exception):
            await session.commit()
        await session.rollback()


class TestSessionModel:
    async def test_create_session(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient
        from verbamind.backend.database.models.psychologist import Psychologist
        from verbamind.backend.database.models.session import Session

        patient = Patient(name="P1", age=30, gender="female")
        psych = Psychologist(name="Dr. P", license_number="LIC-002")
        session.add_all([patient, psych])
        await session.flush()

        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test.vera",
            status="recorded",
        )
        session.add(ses)
        await session.commit()
        await session.refresh(ses)

        assert ses.id is not None
        assert ses.status == "recorded"

    async def test_session_relationship_to_patient(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient
        from verbamind.backend.database.models.psychologist import Psychologist
        from verbamind.backend.database.models.session import Session

        patient = Patient(name="P2", age=28, gender="male")
        psych = Psychologist(name="Dr. Q", license_number="LIC-003")
        session.add_all([patient, psych])
        await session.flush()

        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test2.vera",
        )
        session.add(ses)
        await session.commit()
        await session.refresh(ses)

        assert ses.patient.name == "P2"
        assert ses.psychologist.name == "Dr. Q"


class TestTranscriptModel:
    async def test_create_transcript(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient
        from verbamind.backend.database.models.psychologist import Psychologist
        from verbamind.backend.database.models.session import Session
        from verbamind.backend.database.models.transcript import Transcript

        patient = Patient(name="P3", age=35, gender="male")
        psych = Psychologist(name="Dr. R", license_number="LIC-004")
        session.add_all([patient, psych])
        await session.flush()

        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test3.vera",
        )
        session.add(ses)
        await session.flush()

        transcript = Transcript(
            session_id=ses.id,
            speaker="patient",
            text="Saya merasa cemas akhir-akhir ini.",
            start_time=0.0,
            end_time=3.5,
        )
        session.add(transcript)
        await session.commit()
        await session.refresh(transcript)

        assert transcript.id is not None
        assert transcript.speaker == "patient"


class TestSERResultModel:
    async def test_create_ser_result(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient
        from verbamind.backend.database.models.psychologist import Psychologist
        from verbamind.backend.database.models.ser_result import SERResult
        from verbamind.backend.database.models.session import Session

        patient = Patient(name="P4", age=40, gender="female")
        psych = Psychologist(name="Dr. S", license_number="LIC-005")
        session.add_all([patient, psych])
        await session.flush()

        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test4.vera",
        )
        session.add(ses)
        await session.flush()

        ser = SERResult(
            session_id=ses.id,
            emotion="anxious",
            confidence=0.87,
            segment_start=0.0,
            segment_end=3.5,
        )
        session.add(ser)
        await session.commit()
        await session.refresh(ser)

        assert ser.id is not None
        assert ser.emotion == "anxious"
        assert 0 <= ser.confidence <= 1


class TestBIRPResultModel:
    async def test_create_birp_result(self, session: AsyncSession):
        from verbamind.backend.database.models.birp_result import BIRPResult
        from verbamind.backend.database.models.patient import Patient
        from verbamind.backend.database.models.psychologist import Psychologist
        from verbamind.backend.database.models.session import Session

        patient = Patient(name="P5", age=32, gender="male")
        psych = Psychologist(name="Dr. T", license_number="LIC-006")
        session.add_all([patient, psych])
        await session.flush()

        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test5.vera",
        )
        session.add(ses)
        await session.flush()

        birp = BIRPResult(
            session_id=ses.id,
            behavior="Pasien menunjukkan gejala kecemasan.",
            intervention="Psikolog melakukan CBT.",
            response="Pasien merespons positif.",
            plan="Lanjutkan sesi minggu depan.",
        )
        session.add(birp)
        await session.commit()
        await session.refresh(birp)

        assert birp.id is not None
        assert birp.behavior is not None
        assert birp.intervention is not None
        assert birp.response is not None
        assert birp.plan is not None


class TestAuditLogModel:
    async def test_create_audit_log(self, session: AsyncSession):
        from verbamind.backend.database.models.audit_log import AuditLog

        log = AuditLog(action="session_created", details='{"session_id": 1}')
        session.add(log)
        await session.commit()
        await session.refresh(log)

        assert log.id is not None
        assert log.action == "session_created"


class TestCascadeDelete:
    async def test_delete_session_cascades_transcripts(self, session: AsyncSession):
        from verbamind.backend.database.models.patient import Patient
        from verbamind.backend.database.models.psychologist import Psychologist
        from verbamind.backend.database.models.session import Session
        from verbamind.backend.database.models.transcript import Transcript

        patient = Patient(name="P6", age=30, gender="female")
        psych = Psychologist(name="Dr. U", license_number="LIC-007")
        session.add_all([patient, psych])
        await session.flush()

        ses = Session(
            patient_id=patient.id,
            psychologist_id=psych.id,
            audio_file_path="recordings/test6.vera",
        )
        session.add(ses)
        await session.flush()

        t = Transcript(session_id=ses.id, speaker="patient", text="Test", start_time=0.0, end_time=1.0)
        session.add(t)
        await session.commit()

        await session.delete(ses)
        await session.commit()

        from sqlalchemy import select

        result = await session.execute(select(Transcript).where(Transcript.id == t.id))
        assert result.scalar_one_or_none() is None


class TestAllTablesExist:
    async def test_all_tables_created(self, engine):
        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        required = [
            "patients",
            "psychologists",
            "sessions",
            "transcripts",
            "ser_results",
            "birp_results",
            "audit_logs",
        ]
        for table in required:
            assert table in tables, f"Table {table} not found"
