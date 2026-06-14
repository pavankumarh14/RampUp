from __future__ import annotations

import structlog
import tiktoken

from app.config.settings import settings

logger = structlog.get_logger(__name__)


class TextChunker:
    """Splits raw document text into overlapping token-bounded chunks."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_text(
        self,
        text: str,
        source_url: str,
        source_type: str,
        title: str,
    ) -> list[dict]:
        """
        Split *text* into overlapping chunks and return a list of chunk dicts.

        Each dict contains:
            text            – chunk content
            chunk_index     – zero-based position within the source document
            source_url      – origin URL/identifier
            source_type     – 'sharepoint' | 'teams' | 'onenote' | 'outlook'
            title           – human-readable document title
            metadata        – dict of additional metadata
        """
        if not text.strip():
            return []

        tokens = self.encoding.encode(text)
        chunks: list[dict] = []
        index = 0
        start = 0

        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(
                {
                    "text": chunk_text,
                    "chunk_index": index,
                    "source_url": source_url,
                    "source_type": source_type,
                    "title": title,
                    "metadata": {
                        "token_start": start,
                        "token_end": end,
                    },
                }
            )
            start += self.chunk_size - self.chunk_overlap
            index += 1

        logger.debug(
            "chunker.split",
            source_url=source_url,
            num_chunks=len(chunks),
            chunk_size=self.chunk_size,
        )
        return chunks

    def chunk_document(self, doc: dict) -> list[dict]:
        """
        Convenience wrapper that accepts a document dict and delegates to chunk_text.

        Expected doc keys: text, source_url, source_type, title
        """
        return self.chunk_text(
            text=doc.get("text", ""),
            source_url=doc.get("source_url", ""),
            source_type=doc.get("source_type", "sharepoint"),
            title=doc.get("title", ""),
        )


text_chunker = TextChunker()
