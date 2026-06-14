import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.settings import settings

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages the async SQLAlchemy engine lifecycle."""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None

    async def initialize(self) -> None:
        """Create the async engine, converting the DATABASE_URL to asyncpg scheme."""
        url = settings.DATABASE_URL

        # Ensure we use the asyncpg driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(
            url,
            echo=(settings.APP_ENV == "development"),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        logger.info("database.initialized", url=url.split("@")[-1])  # log host only

    async def close(self) -> None:
        """Dispose the engine and release all connections."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            logger.info("database.closed")

    def get_engine(self) -> AsyncEngine:
        if self.engine is None:
            raise RuntimeError("DatabaseManager has not been initialized. Call initialize() first.")
        return self.engine


db_manager = DatabaseManager()
