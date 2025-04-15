from collections.abc import AsyncGenerator

import logfire
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from sqlalchemy.orm import DeclarativeBase

from src.config.settings import Config

config = Config()

# logfire.configure(token=config.logfire_api_key)

class Base(DeclarativeBase):
    pass

SQLALCHEMY_DATABASE_URI = URL.create(
    drivername="postgresql+asyncpg",
    username=config.postgres_user,
    password=config.postgres_password,
    host=config.postgres_host,
    database=config.postgres_db,
    port=config.postgres_port,
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URI)
async_session = async_sessionmaker(autoflush=False, bind=engine, expire_on_commit=False)

# logfire.instrument_sqlalchemy(engine=engine)

# Dependency to get the database session
async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()