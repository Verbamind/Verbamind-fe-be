"""Session model — represents a recording session."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verbamind.backend.database.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("psychologists.id", ondelete="CASCADE"), nullable=False)
    audio_file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="recorded", server_default="recorded")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    birp_status: Mapped[str] = mapped_column(String(50), nullable=True)
    audio_status: Mapped[str] = mapped_column(String(50), nullable=True)
    consent_file: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="sessions")
    psychologist = relationship("Psychologist", back_populates="sessions")
    transcripts = relationship("Transcript", back_populates="session", cascade="all, delete-orphan")
    nonverbal_results = relationship("NonverbalResult", back_populates="session", cascade="all, delete-orphan")
    birp_result = relationship("BIRPResult", back_populates="session", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session id={self.id} status='{self.status}'>"
