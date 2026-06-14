from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.settings import settings
from app.core.database import db_manager
from app.core.orm import build_session_maker

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    # ----- startup -----
    logger.info("rampup.startup", env=settings.APP_ENV)
    await db_manager.initialize()
    build_session_maker()
    logger.info("rampup.ready")

    yield

    # ----- shutdown -----
    logger.info("rampup.shutdown")
    await db_manager.close()


app = FastAPI(
    title="RampUp",
    description=(
        "AI-Powered New Hire Knowledge Accelerator. "
        "Ingests M365 documents via MS Graph API and answers onboarding questions "
        "using RAG over pgvector + Azure OpenAI."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(router, prefix="/api")


# ---------------------------------------------------------------------------
# Root health check
# ---------------------------------------------------------------------------


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "service": "RampUp",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs",
    }
