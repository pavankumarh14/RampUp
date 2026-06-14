from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.config.settings import settings
from app.core.database import db_manager
from app.core.orm import build_session_maker

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    # ----- startup -----
    # Log DATABASE_URL (without password)
    safe_url = settings.DATABASE_URL
    # Hide password if present
    if "@" in safe_url:
        protocol, rest = safe_url.split("@", 1)
        if "://" in protocol:
            scheme, userinfo = protocol.split("://", 1)
            if ":" in userinfo:
                username, _ = userinfo.split(":", 1)
                safe_url = f"{scheme}://{username}:***@{rest}"
    logger.info("database.url", url=safe_url)
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
# Serve frontend
# ---------------------------------------------------------------------------
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ---------------------------------------------------------------------------
# Root health check (fallback if frontend is not built)
# ---------------------------------------------------------------------------


@app.get("/", tags=["root"], include_in_schema=False)
async def root():
    if frontend_dir.exists() and (frontend_dir / "index.html").exists():
        return FileResponse(frontend_dir / "index.html")
    return {
        "service": "RampUp",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs",
    }
