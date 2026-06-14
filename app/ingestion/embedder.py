from __future__ import annotations

import uuid

import structlog
from openai import AsyncAzureOpenAI, AsyncOpenAI
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings

logger = structlog.get_logger(__name__)

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class EmbeddingService:
    """Wraps LLM provider embeddings and persists chunks to pgvector."""

    def __init__(self) -> None:
        self._client: AsyncAzureOpenAI | AsyncOpenAI | None = None

    def _get_client(self) -> AsyncAzureOpenAI | AsyncOpenAI:
        if self._client is None:
            provider = settings.LLM_PROVIDER.lower()
            if provider == "openai":
                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            elif provider == "gemini":
                self._client = AsyncOpenAI(
                    base_url=_GEMINI_BASE_URL,
                    api_key=settings.GEMINI_API_KEY,
                )
            else:
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                )
        return self._client

    def _get_embedding_model(self) -> str:
        provider = settings.LLM_PROVIDER.lower()
        if provider == "openai":
            return settings.OPENAI_EMBEDDING_MODEL
        if provider == "gemini":
            return settings.GEMINI_EMBEDDING_MODEL
        return settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT

    async def embed_text(self, text: str) -> list[float]:
        """
        Embed a single string using the configured provider.
        """
        client = self._get_client()
        response = await client.embeddings.create(
            input=text,
            model=self._get_embedding_model(),
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of strings in a single API call.

        Azure/OpenAI support up to 2048 inputs per request for
        text-embedding-3-large; callers should batch accordingly.
        """
        if not texts:
            return []

        client = self._get_client()
        response = await client.embeddings.create(
            input=texts,
            model=self._get_embedding_model(),
        )
        sorted_data = sorted(response.data, key=lambda d: d.index)
        return [item.embedding for item in sorted_data]

    async def upsert_chunks(
        self,
        session: AsyncSession,
        chunks: list[dict],
    ) -> None:
        """
        Embed all chunks and persist them to the document_chunk table with upsert
        support (overwrite existing chunks with same source_url and chunk_index).
        """
        from app.core.orm import DocumentChunk

        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        logger.info("embedder.upsert_chunks.start", num_chunks=len(chunks))

        embeddings = await self.embed_batch(texts)

        values = []
        for chunk, embedding in zip(chunks, embeddings):
            values.append(
                {
                    "id": str(uuid.uuid4()),
                    "source_url": chunk["source_url"],
                    "source_type": chunk["source_type"],
                    "title": chunk.get("title", ""),
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "embedding": embedding,
                    "metadata_json": chunk.get("metadata"),
                }
            )

        stmt = insert(DocumentChunk).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_url", "chunk_index"],
            set_={
                "text": stmt.excluded.text,
                "embedding": stmt.excluded.embedding,
                "title": stmt.excluded.title,
                "metadata_json": stmt.excluded.metadata_json,
            },
        )

        await session.execute(stmt)
        await session.flush()

        logger.info("embedder.upsert_chunks.done", num_inserted=len(values))


embedding_service = EmbeddingService()
