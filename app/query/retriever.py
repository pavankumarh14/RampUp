from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings

logger = structlog.get_logger(__name__)


class VectorRetriever:
    """Performs cosine-similarity vector search against the document_chunk table."""

    async def search(
        self,
        session: AsyncSession,
        query_embedding: list[float],
        top_k: int = settings.TOP_K_RESULTS,
    ) -> list[dict]:
        """
        Retrieve the *top_k* most similar chunks to *query_embedding*.

        Uses pgvector's <=> operator (cosine distance) so that lower distance
        means higher similarity.  Chunks below the similarity threshold are
        filtered out before returning.

        Returns a list of dicts:
            text            – chunk content
            source_url      – origin document URL
            source_type     – data source category
            title           – document title
            chunk_index     – position within source document
            similarity_score – float in [0, 1]; 1 = identical
        """
        from app.core.orm import DocumentChunk  # local import

        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)

        stmt = (
            select(
                DocumentChunk.text,
                DocumentChunk.source_url,
                DocumentChunk.source_type,
                DocumentChunk.title,
                DocumentChunk.chunk_index,
                distance_expr.label("distance"),
            )
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(top_k)
        )

        rows = (await session.execute(stmt)).all()

        results: list[dict] = []
        for row in rows:
            similarity = 1.0 - float(row.distance)
            if similarity < settings.SIMILARITY_THRESHOLD:
                continue
            results.append(
                {
                    "text": row.text,
                    "source_url": row.source_url,
                    "source_type": row.source_type,
                    "title": row.title,
                    "chunk_index": row.chunk_index,
                    "similarity_score": round(similarity, 4),
                }
            )

        logger.debug(
            "retriever.search.done",
            top_k=top_k,
            returned=len(results),
            threshold=settings.SIMILARITY_THRESHOLD,
        )
        return results

    async def log_knowledge_gap(
        self,
        session: AsyncSession,
        query_text: str,
        topic_category: str | None = None,
    ) -> None:
        """Insert a KnowledgeGap record for queries that could not be answered."""
        from app.core.orm import KnowledgeGap  # local import

        gap = KnowledgeGap(
            id=str(uuid.uuid4()),
            query_text=query_text,
            topic_category=topic_category,
            resolved=False,
        )
        session.add(gap)
        await session.flush()

        logger.info(
            "retriever.knowledge_gap.logged",
            query_text=query_text[:120],
            gap_id=gap.id,
        )


retriever = VectorRetriever()
