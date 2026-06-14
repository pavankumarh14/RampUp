import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

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

        logger.info("database.connecting", url=url.split("@")[-1])  # log host only

        retry_count = 0
        max_retries = 5
        retry_delay = 2
        while retry_count < max_retries:
            try:
                self.engine = create_async_engine(
                    url,
                    echo=(settings.APP_ENV == "development"),
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                )

                # Try a simple query to verify connection
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                    await conn.commit()

                logger.info("database.initialized", url=url.split("@")[-1])
                break

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning("database.connection.failed", error=str(e), retry_count=retry_count, max_retries=max_retries)
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("database.connection.failed.final", error=str(e))
                    raise

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
