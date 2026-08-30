"""NonverbalResult model — per-frame loudness + pitch analysis from SpeechToNonverbalInformation pipeline.

Replaces the old SERResult table. Stores frame-level nonverbal cue data
from Verbamind_SpeechToNonverbalInformation pipeline.
"""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verbamind.backend.database.base import Base


class NonverbalResult(Base):
    __tablename__ = "nonverbal_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    frame: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)

    # Loudness (dB)
    current_loudness: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_loudness: Mapped[float] = mapped_column(Float, nullable=False)
    delta_loudness: Mapped[float] = mapped_column(Float, nullable=False)
    loudness_category: Mapped[str] = mapped_column(String(50), nullable=False)

    # Pitch (Hz) — nullable for unvoiced frames
    current_pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta_pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    pitch_category: Mapped[str] = mapped_column(String(50), nullable=False)

    session = relationship("Session", back_populates="nonverbal_results")

    def __repr__(self) -> str:
        return f"<NonverbalResult id={self.id} frame={self.frame} loud={self.loudness_category}>"
