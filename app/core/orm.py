from datetime import datetime
from typing import AsyncGenerator

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.database import db_manager


class Base(DeclarativeBase):
    pass


class DocumentChunk(Base):
    """A single text chunk derived from an ingested M365 document."""

    __tablename__ = "document_chunk"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="One of: sharepoint | teams | onenote | outlook",
    )
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(3072), nullable=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KnowledgeGap(Base):
    """A query that could not be answered confidently from the knowledge base."""

    __tablename__ = "knowledge_gap"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ---------------------------------------------------------------------------
# Session factory – built lazily after db_manager.initialize() is called
# ---------------------------------------------------------------------------

async_session_maker: async_sessionmaker[AsyncSession] | None = None


def build_session_maker() -> async_sessionmaker[AsyncSession]:
    """Call this once the engine has been initialized."""
    global async_session_maker
    async_session_maker = async_sessionmaker(
        bind=db_manager.get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    if async_session_maker is None:
        raise RuntimeError("Session maker not initialized. Call build_session_maker() first.")
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
