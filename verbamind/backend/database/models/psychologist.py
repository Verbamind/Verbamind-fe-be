"""Psychologist model."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from verbamind.backend.database.base import Base


class Psychologist(Base):
    __tablename__ = "psychologists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=True)

    sessions = relationship("Session", back_populates="psychologist", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Psychologist id={self.id} name='{self.name}'>"
