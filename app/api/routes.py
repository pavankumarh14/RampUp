from __future__ import annotations

from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.orm import KnowledgeGap, get_session
from app.ingestion.chunker import text_chunker
from app.ingestion.embedder import embedding_service
from app.ingestion.graph_client import graph_client
from app.query.generator import generator
from app.query.retriever import retriever

logger = structlog.get_logger(__name__)

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_session)]


class IngestRequest(BaseModel):
    source_type: Optional[str] = Field(
        None,
        description="Data source type: 'sharepoint' or 'teams' (for synthetic data)",
    )
    site_id: Optional[str] = Field(
        None,
        description="SharePoint site ID or Teams team ID (for synthetic data)",
    )
    source_url: Optional[str] = Field(
        None,
        description="URL of the document to ingest (manual mode)",
    )
    title: Optional[str] = Field(
        None,
        description="Title of the document (manual mode)",
    )
    text: Optional[str] = Field(
        None,
        description="Raw text content to ingest (manual mode)",
    )


class IngestResponse(BaseModel):
    status: str
    message: str
    num_chunks: Optional[int] = None


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language question to answer from the knowledge base",
    )


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: str


class KnowledgeGapOut(BaseModel):
    id: str
    query_text: str
    topic_category: str | None
    reported_at: str
    resolved: bool


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest documents into the knowledge base",
    status_code=status.HTTP_200_OK,
)
async def ingest(
    body: IngestRequest,
    session: DbSession,
) -> IngestResponse:
    """
    Ingest documents: either from synthetic M365 data OR manual text input!
    """
    logger.info("routes.ingest.called", body=body)

    docs_to_ingest = []

    # Case 1: Manual text input
    if body.text:
        docs_to_ingest.append(
            {
                "text": body.text,
                "source_url": body.source_url or "manual://" + str(hash(body.text)),
                "source_type": "manual",
                "title": body.title or "Manual Ingestion",
            }
        )

    # Case 2: Synthetic data from graph client
    elif body.source_type and body.site_id:
        if body.source_type == "sharepoint":
            docs_to_ingest = await graph_client.list_sharepoint_documents(body.site_id)
        elif body.source_type == "teams":
            docs_to_ingest = await graph_client.get_teams_transcripts(body.site_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source_type: {body.source_type}. Must be 'sharepoint' or 'teams'.",
            )

    # Case 3: No valid input
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either provide 'text' or both 'source_type' and 'site_id' to ingest data.",
        )

    total_chunks = 0
    for doc in docs_to_ingest:
        chunks = text_chunker.chunk_document(doc)
        await embedding_service.upsert_chunks(session, chunks)
        total_chunks += len(chunks)

    return IngestResponse(
        status="success",
        message=f"Successfully ingested {len(docs_to_ingest)} document(s) into {total_chunks} chunks.",
        num_chunks=total_chunks,
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a question answered from the knowledge base",
)
async def query(
    body: QueryRequest,
    session: DbSession,
) -> QueryResponse:
    """
    Embed the question, retrieve relevant chunks via pgvector cosine search,
    and synthesise a grounded answer with GPT-4o.

    If no confident answer can be found, the query is logged as a knowledge gap.
    """
    logger.info("routes.query.called", question=body.question[:80])

    try:
        query_embedding = await embedding_service.embed_text(body.question)
    except Exception as exc:
        logger.error("routes.query.embed_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding service error: {exc}",
        ) from exc

    chunks = await retriever.search(session, query_embedding)

    try:
        result = await generator.generate(body.question, chunks)
    except Exception as exc:
        logger.error("routes.query.generate_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Generation service error: {exc}",
        ) from exc

    if result["confidence"] == "not_found":
        await retriever.log_knowledge_gap(session, body.question)

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
    )


@router.get(
    "/gaps",
    response_model=list[KnowledgeGapOut],
    summary="List unresolved knowledge gaps",
)
async def list_gaps(
    session: DbSession,
    resolved: bool = False,
) -> list[KnowledgeGapOut]:
    """
    Return knowledge gap records. Pass `?resolved=true` to include resolved gaps.
    """
    stmt = select(KnowledgeGap).order_by(KnowledgeGap.reported_at.desc())
    if not resolved:
        stmt = stmt.where(KnowledgeGap.resolved.is_(False))

    rows = (await session.execute(stmt)).scalars().all()

    return [
        KnowledgeGapOut(
            id=row.id,
            query_text=row.query_text,
            topic_category=row.topic_category,
            reported_at=row.reported_at.isoformat(),
            resolved=row.resolved,
        )
        for row in rows
    ]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
