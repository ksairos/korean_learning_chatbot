from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from sqlalchemy.orm import DeclarativeBase

from src.config.settings import Config

config = Config()

# logfire.configure(token=config.logfire_api_key)

class Base(DeclarativeBase):
    pass

engine = create_async_engine(config.asyncpg_url.unicode_string())
async_session = async_sessionmaker(autoflush=False, bind=engine, expire_on_commit=False)

# logfire.instrument_sqlalchemy(engine=engine)

# Dependency to get the database session
async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()