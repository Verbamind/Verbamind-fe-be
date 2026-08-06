"""SER Result model — Speech Emotion Recognition output."""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verbamind.backend.database.base import Base


class SERResult(Base):
    __tablename__ = "ser_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    emotion: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    segment_start: Mapped[float] = mapped_column(Float, nullable=False)
    segment_end: Mapped[float] = mapped_column(Float, nullable=False)

    session = relationship("Session", back_populates="ser_results")

    def __repr__(self) -> str:
        return f"<SERResult id={self.id} emotion='{self.emotion}'>"
