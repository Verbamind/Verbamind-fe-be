"""Async SQLAlchemy engine and session factory for SQLite."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from verbamind.config.config import get_database_url

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        _engine = create_async_engine(url, echo=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory
