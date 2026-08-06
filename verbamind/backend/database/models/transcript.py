"""Transcript model — speech-to-text segments."""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verbamind.backend.database.base import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    speaker: Mapped[str] = mapped_column(String(50), nullable=False)
    text: Mapped[str] = mapped_column(String(5000), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)

    session = relationship("Session", back_populates="transcripts")

    def __repr__(self) -> str:
        return f"<Transcript id={self.id} speaker='{self.speaker}'>"
