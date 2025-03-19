import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Type, TypeVar, Any

from sqlalchemy import Column, DateTime, Integer, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base, DeclarativeMeta

logger = logging.getLogger(__name__)

# Global engine reference
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None

# Create base model class
Base = declarative_base()

# Type variable for ORM models
T = TypeVar("T", bound=DeclarativeMeta)


class BaseModel:
    """Base model class to replace BaseOrmTable."""

    id = Column(Integer, primary_key=True, autoincrement=True)


class BaseModelWithTS(BaseModel):
    """Base model with timestamp columns to replace BaseOrmTableWithTS."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


async def init_db(
    host: str, port: int, user: str, password: str, db_name: str, echo: bool = False
) -> None:
    """Initialize database connection."""
    global engine, async_session_factory

    connection_string = f"mysql+asyncmy://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_async_engine(connection_string, echo=echo)
    async_session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )


async def create_database_if_not_exists(
    host: str, port: int, user: str, password: str, db_name: str
) -> None:
    """Create database if it doesn't exist."""
    engine_without_db = create_async_engine(
        f"mysql+asyncmy://{user}:{password}@{host}:{port}/",
        echo=True,
    )
    async with engine_without_db.begin() as conn:
        query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
        logger.info(f"SQL Query: {query}, Context: Creating database")
        await conn.execute(text(query))
    await engine_without_db.dispose()


async def create_tables() -> None:
    """Create all tables defined in the models."""
    if engine is None:
        raise RuntimeError("Database engine not initialized")

    async with engine.begin() as conn:
        logger.info("Context: Creating tables")
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a session for database operations."""
    if async_session_factory is None:
        raise RuntimeError("Session factory not initialized")

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


class DbOperations:
    """Class to replace DBManager for common database operations."""

    @staticmethod
    async def create(model: Type[T], **kwargs) -> T:
        """Create a new record."""
        async for session in get_session():
            instance = model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    @staticmethod
    async def get_by_id(model: Type[T], id: int) -> Optional[T]:
        """Get record by ID."""
        async for session in get_session():
            return await session.get(model, id)

    @staticmethod
    async def update(model: Type[T], id: int, **kwargs) -> Optional[T]:
        """Update a record by ID."""
        async for session in get_session():
            instance = await session.get(model, id)
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                await session.commit()
                await session.refresh(instance)
            return instance

    @staticmethod
    async def delete(model: Type[T], id: int) -> bool:
        """Delete a record by ID."""
        async for session in get_session():
            instance = await session.get(model, id)
            if instance:
                await session.delete(instance)
                await session.commit()
                return True
            return False

    @staticmethod
    async def execute(query: Any) -> Any:
        """Execute a custom query."""
        async for session in get_session():
            result = await session.execute(query)
            return result
