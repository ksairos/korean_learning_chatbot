from collections.abc import AsyncGenerator

import logfire
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from src.config.settings import Config

config = Config()

# logfire.configure(token=config.logfire_api_key)


class Base(DeclarativeBase):
    pass

# Async engine and session factory
engine = create_async_engine(config.asyncpg_url.unicode_string(), pool_size=10, max_overflow=20, pool_timeout=60)
async_session = async_sessionmaker(autoflush=False, bind=engine, expire_on_commit=False)

# Sync engine and session factory for scripts and testing
sync_engine = create_engine(config.sync_pg_url.unicode_string())
sync_session = sessionmaker(autoflush=False, bind=sync_engine, expire_on_commit=False)

# logfire.instrument_sqlalchemy(engine=engine)


# Dependency to get the async database session
async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# Function to get a synchronous database session
def get_sync_db() -> Session | None:
    session = sync_session()
    try:
        return session
    finally:
        session.close()
