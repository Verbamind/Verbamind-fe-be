"""Declarative base and table creation utilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


async def init_db(session: AsyncSession) -> None:
    from verbamind.backend.database.connection import get_engine

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
