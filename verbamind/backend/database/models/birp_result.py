"""BIRP Result model — AI-generated clinical documentation."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verbamind.backend.database.base import Base


class BIRPResult(Base):
    __tablename__ = "birp_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    behavior: Mapped[str] = mapped_column(String(5000), nullable=False)
    intervention: Mapped[str] = mapped_column(String(5000), nullable=False)
    response: Mapped[str] = mapped_column(String(5000), nullable=False)
    plan: Mapped[str] = mapped_column(String(5000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="birp_result")

    def __repr__(self) -> str:
        return f"<BIRPResult id={self.id} session_id={self.session_id}>"
